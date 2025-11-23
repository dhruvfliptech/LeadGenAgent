import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowLeftIcon,
  PlusIcon,
  CheckCircleIcon,
  XCircleIcon,
  PencilIcon,
  BeakerIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline'
import { mockApprovalRules, ApprovalRule } from '@/mocks/approvals.mock'
import RiskIndicator from '@/components/approvals/RiskIndicator'
import toast from 'react-hot-toast'

export default function ApprovalRules() {
  const [rules, setRules] = useState(mockApprovalRules)
  const [showRuleEditor, setShowRuleEditor] = useState(false)
  const [editingRule, setEditingRule] = useState<ApprovalRule | null>(null)

  const handleToggleRule = (ruleId: string) => {
    setRules(prev => prev.map(r =>
      r.rule_id === ruleId ? { ...r, enabled: !r.enabled } : r
    ))
    const rule = rules.find(r => r.rule_id === ruleId)
    toast.success(`Rule ${rule?.enabled ? 'disabled' : 'enabled'}`)
  }

  const handleTestRule = (rule: ApprovalRule) => {
    toast.success(`Testing rule: ${rule.name}`)
    // Mock test implementation
  }

  const handleEditRule = (rule: ApprovalRule) => {
    setEditingRule(rule)
    setShowRuleEditor(true)
  }

  const handleCreateRule = () => {
    setEditingRule(null)
    setShowRuleEditor(true)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Link
          to="/approvals"
          className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeftIcon className="w-4 h-4" />
          Back to Approvals
        </Link>

        <div className="md:flex md:items-center md:justify-between">
          <div className="flex-1 min-w-0">
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
              <Cog6ToothIcon className="w-8 h-8 text-gray-500" />
              Approval Rules
            </h1>
            <p className="mt-1 text-gray-600">
              Configure automated approval workflows based on risk levels and conditions
            </p>
          </div>
          <div className="mt-4 md:mt-0">
            <button
              onClick={handleCreateRule}
              className="btn-primary inline-flex items-center gap-2"
            >
              <PlusIcon className="w-4 h-4" />
              Create Rule
            </button>
          </div>
        </div>
      </div>

      {/* Rules Table */}
      <div className="card">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rule Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Risk Level
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Conditions
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {rules.map((rule) => (
                <tr key={rule.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900">
                      {rule.name}
                    </div>
                    <div className="text-sm text-gray-500">
                      {rule.description}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-gray-900">
                      {rule.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <RiskIndicator level={rule.risk_level} showScore={false} size="sm" />
                  </td>
                  <td className="px-6 py-4">
                    {rule.conditions.length > 0 ? (
                      <div className="text-sm text-gray-900">
                        {rule.conditions.length} condition{rule.conditions.length !== 1 ? 's' : ''}
                      </div>
                    ) : (
                      <span className="text-sm text-gray-500">Always</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <button
                      onClick={() => handleToggleRule(rule.rule_id)}
                      className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${
                        rule.enabled
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {rule.enabled ? (
                        <>
                          <CheckCircleIcon className="w-3 h-3" />
                          Enabled
                        </>
                      ) : (
                        <>
                          <XCircleIcon className="w-3 h-3" />
                          Disabled
                        </>
                      )}
                    </button>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => handleTestRule(rule)}
                        className="text-gray-600 hover:text-gray-900 inline-flex items-center gap-1"
                      >
                        <BeakerIcon className="w-4 h-4" />
                        Test
                      </button>
                      <button
                        onClick={() => handleEditRule(rule)}
                        className="text-blue-600 hover:text-blue-700 inline-flex items-center gap-1"
                      >
                        <PencilIcon className="w-4 h-4" />
                        Edit
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Rule Editor Modal */}
      {showRuleEditor && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">
                {editingRule ? 'Edit Rule' : 'Create New Rule'}
              </h2>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Rule Name
                </label>
                <input
                  type="text"
                  className="form-input w-full"
                  defaultValue={editingRule?.name}
                  placeholder="e.g., High-value email responses"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  className="form-input w-full"
                  rows={2}
                  defaultValue={editingRule?.description}
                  placeholder="Brief description of what this rule does"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Type
                  </label>
                  <select className="form-input w-full" defaultValue={editingRule?.type}>
                    <option value="email_response">Email Response</option>
                    <option value="email_campaign">Email Campaign</option>
                    <option value="lead_action">Lead Action</option>
                    <option value="demo_site_deploy">Demo Site Deploy</option>
                    <option value="video_publish">Video Publish</option>
                    <option value="workflow_trigger">Workflow Trigger</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Risk Level
                  </label>
                  <select className="form-input w-full" defaultValue={editingRule?.risk_level}>
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Requires Approval
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    className="form-checkbox"
                    defaultChecked={editingRule?.requires_approval ?? true}
                  />
                  <span className="text-sm text-gray-600">
                    Require manual approval when this rule matches
                  </span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Auto-approve After (hours)
                </label>
                <input
                  type="number"
                  className="form-input w-full"
                  defaultValue={editingRule?.auto_approve_after_hours}
                  placeholder="Optional - leave empty to never auto-approve"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Approvers (comma-separated emails)
                </label>
                <input
                  type="text"
                  className="form-input w-full"
                  defaultValue={editingRule?.approvers.join(', ')}
                  placeholder="user1@example.com, user2@example.com"
                />
              </div>

              <div className="border-t border-gray-200 pt-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Conditions (optional)
                </label>
                <div className="text-sm text-gray-500 mb-2">
                  Define conditions that must be met for this rule to trigger
                </div>
                {editingRule?.conditions && editingRule.conditions.length > 0 ? (
                  <div className="space-y-2 mb-2">
                    {editingRule.conditions.map((condition, idx) => (
                      <div key={idx} className="bg-gray-50 p-3 rounded border border-gray-200">
                        <div className="text-sm">
                          <span className="font-medium">{condition.field}</span>{' '}
                          <span className="text-gray-600">{condition.operator}</span>{' '}
                          <span className="font-medium">{String(condition.value)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : null}
                <button className="btn-secondary text-sm">
                  <PlusIcon className="w-4 h-4 inline mr-1" />
                  Add Condition
                </button>
              </div>
            </div>

            <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
              <button
                onClick={() => setShowRuleEditor(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  toast.success(editingRule ? 'Rule updated' : 'Rule created')
                  setShowRuleEditor(false)
                }}
                className="btn-primary"
              >
                {editingRule ? 'Update Rule' : 'Create Rule'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
