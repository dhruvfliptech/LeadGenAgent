#!/usr/bin/env python3
"""
Test the Advanced Analytics System.
"""

import asyncio
from datetime import datetime, timedelta
from app.core.database import AsyncSessionLocal
from app.models.leads import Lead
from app.services.analytics_engine import AnalyticsEngine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_analytics():
    """Test the advanced analytics system."""
    print("\n" + "="*60)
    print("TESTING ADVANCED ANALYTICS SYSTEM")
    print("="*60)
    
    async with AsyncSessionLocal() as db:
        try:
            # Step 1: Initialize analytics engine
            print("\n[1] Initializing analytics engine...")
            
            analytics = AnalyticsEngine(db)
            await analytics.initialize()
            
            print("✅ Initialized analytics engine")
            print(f"   Available metrics: {len(analytics.available_metrics)}")
            print(f"   Dashboards: {analytics.dashboard_count}")
            
            # Step 2: Real-time metrics
            print("\n[2] Testing real-time metrics...")
            
            metrics = await analytics.get_real_time_metrics()
            
            print("   Real-Time Metrics:")
            print(f"      Active leads: {metrics['active_leads']}")
            print(f"      Response rate: {metrics['response_rate']:.1%}")
            print(f"      Avg qualification score: {metrics['avg_qualification_score']:.2f}")
            print(f"      Leads per hour: {metrics['leads_per_hour']:.1f}")
            print(f"      System health: {metrics['system_health']}")
            
            # Step 3: Performance analytics
            print("\n[3] Testing performance analytics...")
            
            performance = await analytics.analyze_performance(
                time_range="last_7_days",
                metrics=['conversion_rate', 'response_time', 'quality_score']
            )
            
            print("   Performance Analytics:")
            print(f"      Conversion rate: {performance['conversion_rate']:.1%}")
            print(f"      Avg response time: {performance['avg_response_time']} mins")
            print(f"      Quality score: {performance['quality_score']:.2f}")
            print(f"      Trend: {performance['trend']}")
            print(f"      Improvement: {performance['improvement']:.1%}")
            
            # Step 4: Predictive analytics
            print("\n[4] Testing predictive analytics...")
            
            predictions = await analytics.predict_outcomes(
                forecast_days=7,
                confidence_level=0.95
            )
            
            print("   Predictions (Next 7 Days):")
            print(f"      Expected leads: {predictions['expected_leads']}")
            print(f"      Predicted conversions: {predictions['predicted_conversions']}")
            print(f"      Success probability: {predictions['success_probability']:.1%}")
            print(f"      Confidence interval: [{predictions['ci_lower']}, {predictions['ci_upper']}]")
            print(f"      Risk factors: {predictions['risk_factors'][:2]}")
            
            # Step 5: A/B testing analytics
            print("\n[5] Testing A/B testing analytics...")
            
            ab_results = await analytics.analyze_ab_test(
                test_name="response_template_v2",
                control_group="template_v1",
                variant_group="template_v2"
            )
            
            print("   A/B Test Results:")
            print(f"      Control conversion: {ab_results['control_conversion']:.1%}")
            print(f"      Variant conversion: {ab_results['variant_conversion']:.1%}")
            print(f"      Lift: {ab_results['lift']:.1%}")
            print(f"      Statistical significance: {ab_results['p_value']:.3f}")
            print(f"      Winner: {ab_results['winner']}")
            print(f"      Confidence: {ab_results['confidence']:.1%}")
            
            # Step 6: Lead scoring analytics
            print("\n[6] Testing lead scoring analytics...")
            
            scoring = await analytics.analyze_lead_scoring(
                model_version="v2",
                sample_size=100
            )
            
            print("   Lead Scoring Analytics:")
            print(f"      Model accuracy: {scoring['accuracy']:.1%}")
            print(f"      Precision: {scoring['precision']:.1%}")
            print(f"      Recall: {scoring['recall']:.1%}")
            print(f"      F1 score: {scoring['f1_score']:.2f}")
            print(f"      Feature importance:")
            for feature, importance in scoring['feature_importance'][:3]:
                print(f"         - {feature}: {importance:.2f}")
            
            # Step 7: User behavior analytics
            print("\n[7] Testing user behavior analytics...")
            
            behavior = await analytics.analyze_user_behavior(
                user_segment="power_users",
                time_range="last_30_days"
            )
            
            print("   User Behavior Analytics:")
            print(f"      Active users: {behavior['active_users']}")
            print(f"      Avg session duration: {behavior['avg_session_duration']} mins")
            print(f"      Actions per session: {behavior['actions_per_session']:.1f}")
            print(f"      Most common actions: {behavior['top_actions'][:3]}")
            print(f"      Engagement score: {behavior['engagement_score']:.2f}")
            
            # Step 8: Revenue analytics
            print("\n[8] Testing revenue analytics...")
            
            revenue = await analytics.analyze_revenue(
                include_projections=True,
                breakdown_by="lead_source"
            )
            
            print("   Revenue Analytics:")
            print(f"      Total revenue: ${revenue['total_revenue']:,.2f}")
            print(f"      MRR: ${revenue['mrr']:,.2f}")
            print(f"      ARR: ${revenue['arr']:,.2f}")
            print(f"      Customer LTV: ${revenue['customer_ltv']:,.2f}")
            print(f"      CAC: ${revenue['cac']:,.2f}")
            print(f"      Revenue by source:")
            for source, amount in revenue['breakdown'].items():
                print(f"         - {source}: ${amount:,.2f}")
            
            # Step 9: Generate comprehensive report
            print("\n[9] Generating comprehensive analytics report...")
            
            report = await analytics.generate_report(
                report_type="executive_summary",
                include_visualizations=True,
                format="json"
            )
            
            print("   Report Generated:")
            print(f"      Sections: {len(report['sections'])}")
            print(f"      Metrics included: {report['metrics_count']}")
            print(f"      Visualizations: {report['visualization_count']}")
            print(f"      Key insights: {len(report['insights'])}")
            print(f"      Recommendations: {len(report['recommendations'])}")
            
            # Step 10: Export analytics
            print("\n[10] Testing analytics export...")
            
            export = await analytics.export_analytics(
                format="csv",
                include_raw_data=False
            )
            
            print("   Export Summary:")
            print(f"      Format: {export['format']}")
            print(f"      File size: {export['size_kb']} KB")
            print(f"      Rows exported: {export['row_count']}")
            print(f"      Export path: {export['path']}")
            
            print("\n" + "="*60)
            print("SUMMARY")
            print("="*60)
            print("\n✅ Advanced Analytics System Working!")
            print("\nCapabilities demonstrated:")
            print("  • Real-time metrics monitoring")
            print("  • Performance analytics")
            print("  • Predictive analytics & forecasting")
            print("  • A/B testing analysis")
            print("  • Lead scoring analytics")
            print("  • User behavior tracking")
            print("  • Revenue analytics")
            print("  • Comprehensive reporting")
            print("  • Data export capabilities")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            logger.exception("Test failed")
            return False


if __name__ == "__main__":
    success = asyncio.run(test_analytics())
    
    if success:
        print("\n🎉 Phase 3.2 Advanced Analytics Complete!")
        print("\nFeatures implemented:")
        print("  ✅ Real-time metrics dashboard")
        print("  ✅ Performance tracking")
        print("  ✅ Predictive analytics")
        print("  ✅ A/B testing framework")
        print("  ✅ Lead scoring analytics")
        print("  ✅ User behavior analysis")
        print("  ✅ Revenue tracking")
        print("  ✅ Automated reporting")
        print("  ✅ Data export tools")
    else:
        print("\n⚠️ Analytics test failed")
    
    exit(0 if success else 1)