#!/usr/bin/env python3
"""
n8n Workflow Manager
Programmatic interface for managing n8n workflows via API
"""

import os
import sys
import json
import requests
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import time


class N8nWorkflowManager:
    """Manage n8n workflows programmatically"""

    def __init__(self, n8n_url: str, api_key: str):
        """
        Initialize workflow manager

        Args:
            n8n_url: Base URL of n8n instance (e.g., http://localhost:5678)
            api_key: n8n API key for authentication
        """
        self.base_url = n8n_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "X-N8N-API-KEY": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make authenticated request to n8n API"""
        url = f"{self.base_url}/api/v1/{endpoint.lstrip('/')}"
        kwargs['headers'] = self.headers

        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {url}: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            raise

    # Workflow Management

    def list_workflows(self) -> List[Dict]:
        """List all workflows"""
        response = self._request('GET', 'workflows')
        return response.get('data', [])

    def get_workflow(self, workflow_id: str) -> Dict:
        """Get workflow by ID"""
        return self._request('GET', f'workflows/{workflow_id}')

    def create_workflow(self, workflow_data: Dict) -> Dict:
        """Create new workflow"""
        return self._request('POST', 'workflows', json=workflow_data)

    def update_workflow(self, workflow_id: str, workflow_data: Dict) -> Dict:
        """Update existing workflow"""
        return self._request('PATCH', f'workflows/{workflow_id}', json=workflow_data)

    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete workflow"""
        try:
            self._request('DELETE', f'workflows/{workflow_id}')
            return True
        except Exception as e:
            print(f"Error deleting workflow: {e}")
            return False

    def activate_workflow(self, workflow_id: str) -> Dict:
        """Activate a workflow"""
        workflow = self.get_workflow(workflow_id)
        workflow['active'] = True
        return self.update_workflow(workflow_id, workflow)

    def deactivate_workflow(self, workflow_id: str) -> Dict:
        """Deactivate a workflow"""
        workflow = self.get_workflow(workflow_id)
        workflow['active'] = False
        return self.update_workflow(workflow_id, workflow)

    # Import/Export

    def import_workflow(self, workflow_file: str) -> str:
        """
        Import workflow from JSON file

        Args:
            workflow_file: Path to workflow JSON file

        Returns:
            Workflow ID of imported workflow
        """
        with open(workflow_file, 'r') as f:
            workflow_data = json.load(f)

        # Remove ID if present to create new workflow
        if 'id' in workflow_data:
            del workflow_data['id']

        result = self.create_workflow(workflow_data)
        workflow_id = result.get('id')
        print(f"Imported workflow '{result.get('name')}' with ID: {workflow_id}")
        return workflow_id

    def export_workflow(self, workflow_id: str, output_file: str):
        """
        Export workflow to JSON file

        Args:
            workflow_id: ID of workflow to export
            output_file: Path to save workflow JSON
        """
        workflow = self.get_workflow(workflow_id)

        with open(output_file, 'w') as f:
            json.dump(workflow, f, indent=2)

        print(f"Exported workflow to {output_file}")

    def import_all_workflows(self, workflows_dir: str) -> Dict[str, str]:
        """
        Import all workflows from directory

        Args:
            workflows_dir: Directory containing workflow JSON files

        Returns:
            Dictionary mapping filename to workflow ID
        """
        workflows_path = Path(workflows_dir)
        imported = {}

        for workflow_file in workflows_path.glob('*.json'):
            try:
                workflow_id = self.import_workflow(str(workflow_file))
                imported[workflow_file.name] = workflow_id
            except Exception as e:
                print(f"Error importing {workflow_file.name}: {e}")

        return imported

    def export_all_workflows(self, output_dir: str):
        """Export all workflows to directory"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        workflows = self.list_workflows()

        for workflow in workflows:
            workflow_id = workflow['id']
            filename = f"{workflow['name'].lower().replace(' ', '-')}.json"
            output_file = output_path / filename

            try:
                self.export_workflow(workflow_id, str(output_file))
            except Exception as e:
                print(f"Error exporting workflow {workflow_id}: {e}")

    # Execution Management

    def get_executions(self, workflow_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """
        Get workflow executions

        Args:
            workflow_id: Optional workflow ID to filter by
            limit: Maximum number of executions to return
        """
        params = {'limit': limit}
        if workflow_id:
            params['workflowId'] = workflow_id

        response = self._request('GET', 'executions', params=params)
        return response.get('data', [])

    def get_execution(self, execution_id: str) -> Dict:
        """Get execution details"""
        return self._request('GET', f'executions/{execution_id}')

    def delete_execution(self, execution_id: str) -> bool:
        """Delete execution"""
        try:
            self._request('DELETE', f'executions/{execution_id}')
            return True
        except Exception as e:
            print(f"Error deleting execution: {e}")
            return False

    def retry_execution(self, execution_id: str) -> Dict:
        """Retry failed execution"""
        return self._request('POST', f'executions/{execution_id}/retry')

    # Monitoring

    def get_workflow_stats(self, workflow_id: str, days: int = 7) -> Dict:
        """
        Get workflow statistics

        Args:
            workflow_id: Workflow ID
            days: Number of days to look back

        Returns:
            Dictionary with workflow statistics
        """
        executions = self.get_executions(workflow_id, limit=1000)

        # Calculate statistics
        total = len(executions)
        successful = sum(1 for e in executions if e.get('finished') and not e.get('stoppedAt'))
        failed = sum(1 for e in executions if e.get('stoppedAt') and e.get('data', {}).get('resultData', {}).get('error'))

        return {
            'workflow_id': workflow_id,
            'total_executions': total,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'period_days': days
        }

    def get_all_workflow_stats(self) -> List[Dict]:
        """Get statistics for all workflows"""
        workflows = self.list_workflows()
        stats = []

        for workflow in workflows:
            try:
                workflow_stats = self.get_workflow_stats(workflow['id'])
                workflow_stats['name'] = workflow['name']
                workflow_stats['active'] = workflow.get('active', False)
                stats.append(workflow_stats)
            except Exception as e:
                print(f"Error getting stats for {workflow['name']}: {e}")

        return stats

    def get_failed_executions(self, hours: int = 24) -> List[Dict]:
        """Get failed executions in last N hours"""
        executions = self.get_executions(limit=500)
        cutoff_time = datetime.now().timestamp() - (hours * 3600)

        failed = []
        for execution in executions:
            stopped_at = execution.get('stoppedAt')
            if not stopped_at:
                continue

            # Parse timestamp
            try:
                stopped_timestamp = datetime.fromisoformat(stopped_at.replace('Z', '+00:00')).timestamp()
                if stopped_timestamp > cutoff_time:
                    error = execution.get('data', {}).get('resultData', {}).get('error')
                    if error:
                        failed.append({
                            'execution_id': execution['id'],
                            'workflow_id': execution.get('workflowId'),
                            'stopped_at': stopped_at,
                            'error': error.get('message', 'Unknown error')
                        })
            except Exception as e:
                print(f"Error parsing execution: {e}")

        return failed

    # Workflow Operations

    def trigger_workflow(self, workflow_id: str, data: Optional[Dict] = None) -> Dict:
        """
        Manually trigger a workflow

        Args:
            workflow_id: Workflow ID to trigger
            data: Optional data to pass to workflow

        Returns:
            Execution details
        """
        payload = {'workflowId': workflow_id}
        if data:
            payload['data'] = data

        return self._request('POST', 'workflows/run', json=payload)

    def wait_for_execution(self, execution_id: str, timeout: int = 300, poll_interval: int = 5) -> Dict:
        """
        Wait for execution to complete

        Args:
            execution_id: Execution ID to wait for
            timeout: Maximum time to wait in seconds
            poll_interval: How often to check status in seconds

        Returns:
            Final execution details
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            execution = self.get_execution(execution_id)

            if execution.get('finished'):
                return execution

            time.sleep(poll_interval)

        raise TimeoutError(f"Execution {execution_id} did not complete within {timeout} seconds")

    # Batch Operations

    def activate_all_workflows(self, tag: Optional[str] = None):
        """Activate all workflows, optionally filtered by tag"""
        workflows = self.list_workflows()

        for workflow in workflows:
            if tag and tag not in [t.get('name') for t in workflow.get('tags', [])]:
                continue

            try:
                self.activate_workflow(workflow['id'])
                print(f"Activated: {workflow['name']}")
            except Exception as e:
                print(f"Error activating {workflow['name']}: {e}")

    def deactivate_all_workflows(self, tag: Optional[str] = None):
        """Deactivate all workflows, optionally filtered by tag"""
        workflows = self.list_workflows()

        for workflow in workflows:
            if tag and tag not in [t.get('name') for t in workflow.get('tags', [])]:
                continue

            try:
                self.deactivate_workflow(workflow['id'])
                print(f"Deactivated: {workflow['name']}")
            except Exception as e:
                print(f"Error deactivating {workflow['name']}: {e}")

    # Reporting

    def generate_report(self, output_file: Optional[str] = None) -> Dict:
        """Generate comprehensive workflow report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'workflows': [],
            'summary': {}
        }

        workflows = self.list_workflows()
        all_stats = self.get_all_workflow_stats()

        report['workflows'] = all_stats
        report['summary'] = {
            'total_workflows': len(workflows),
            'active_workflows': sum(1 for w in workflows if w.get('active')),
            'inactive_workflows': sum(1 for w in workflows if not w.get('active')),
            'total_executions': sum(s.get('total_executions', 0) for s in all_stats),
            'total_successful': sum(s.get('successful', 0) for s in all_stats),
            'total_failed': sum(s.get('failed', 0) for s in all_stats)
        }

        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Report saved to {output_file}")

        return report


def main():
    """CLI interface for workflow manager"""
    import argparse

    parser = argparse.ArgumentParser(description='n8n Workflow Manager')
    parser.add_argument('--url', required=True, help='n8n base URL')
    parser.add_argument('--api-key', required=True, help='n8n API key')

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # List workflows
    subparsers.add_parser('list', help='List all workflows')

    # Import workflow
    import_parser = subparsers.add_parser('import', help='Import workflow')
    import_parser.add_argument('file', help='Workflow JSON file')

    # Import all
    import_all_parser = subparsers.add_parser('import-all', help='Import all workflows from directory')
    import_all_parser.add_argument('directory', help='Directory containing workflows')

    # Export workflow
    export_parser = subparsers.add_parser('export', help='Export workflow')
    export_parser.add_argument('workflow_id', help='Workflow ID')
    export_parser.add_argument('output', help='Output file')

    # Export all
    export_all_parser = subparsers.add_parser('export-all', help='Export all workflows')
    export_all_parser.add_argument('directory', help='Output directory')

    # Activate
    activate_parser = subparsers.add_parser('activate', help='Activate workflow')
    activate_parser.add_argument('workflow_id', help='Workflow ID')

    # Deactivate
    deactivate_parser = subparsers.add_parser('deactivate', help='Deactivate workflow')
    deactivate_parser.add_argument('workflow_id', help='Workflow ID')

    # Stats
    stats_parser = subparsers.add_parser('stats', help='Get workflow statistics')
    stats_parser.add_argument('--workflow-id', help='Specific workflow ID')

    # Failed executions
    failed_parser = subparsers.add_parser('failed', help='Get failed executions')
    failed_parser.add_argument('--hours', type=int, default=24, help='Hours to look back')

    # Report
    report_parser = subparsers.add_parser('report', help='Generate workflow report')
    report_parser.add_argument('--output', help='Output file')

    args = parser.parse_args()

    # Initialize manager
    manager = N8nWorkflowManager(args.url, args.api_key)

    # Execute command
    if args.command == 'list':
        workflows = manager.list_workflows()
        for workflow in workflows:
            status = "ACTIVE" if workflow.get('active') else "INACTIVE"
            print(f"[{status}] {workflow['name']} (ID: {workflow['id']})")

    elif args.command == 'import':
        workflow_id = manager.import_workflow(args.file)
        print(f"Imported workflow ID: {workflow_id}")

    elif args.command == 'import-all':
        imported = manager.import_all_workflows(args.directory)
        print(f"Imported {len(imported)} workflows")

    elif args.command == 'export':
        manager.export_workflow(args.workflow_id, args.output)

    elif args.command == 'export-all':
        manager.export_all_workflows(args.directory)

    elif args.command == 'activate':
        manager.activate_workflow(args.workflow_id)
        print(f"Activated workflow {args.workflow_id}")

    elif args.command == 'deactivate':
        manager.deactivate_workflow(args.workflow_id)
        print(f"Deactivated workflow {args.workflow_id}")

    elif args.command == 'stats':
        if args.workflow_id:
            stats = manager.get_workflow_stats(args.workflow_id)
            print(json.dumps(stats, indent=2))
        else:
            stats = manager.get_all_workflow_stats()
            for stat in stats:
                print(f"\n{stat['name']}:")
                print(f"  Total: {stat['total_executions']}")
                print(f"  Success: {stat['successful']}")
                print(f"  Failed: {stat['failed']}")
                print(f"  Success Rate: {stat['success_rate']:.2f}%")

    elif args.command == 'failed':
        failed = manager.get_failed_executions(args.hours)
        print(f"Found {len(failed)} failed executions in last {args.hours} hours")
        for execution in failed:
            print(f"\nExecution ID: {execution['execution_id']}")
            print(f"  Workflow: {execution['workflow_id']}")
            print(f"  Stopped: {execution['stopped_at']}")
            print(f"  Error: {execution['error']}")

    elif args.command == 'report':
        report = manager.generate_report(args.output)
        if not args.output:
            print(json.dumps(report, indent=2))

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
