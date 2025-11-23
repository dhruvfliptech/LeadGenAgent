import {
  IExecuteFunctions,
  INodeExecutionData,
  INodeType,
  INodeTypeDescription,
  ILoadOptionsFunctions,
  INodePropertyOptions,
  NodeOperationError,
} from 'n8n-workflow';

import { OptionsWithUri } from 'request';

export class CraigleadsPro implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'CraigLeads Pro',
    name: 'craigleadsPro',
    icon: 'file:craigleads.svg',
    group: ['transform'],
    version: 1,
    subtitle: '={{$parameter["operation"] + ": " + $parameter["resource"]}}',
    description: 'Interact with CraigLeads Pro API for lead generation automation',
    defaults: {
      name: 'CraigLeads Pro',
    },
    inputs: ['main'],
    outputs: ['main'],
    credentials: [
      {
        name: 'craigleadsProApi',
        required: true,
        displayOptions: {
          show: {
            authentication: ['apiKey'],
          },
        },
      },
    ],
    properties: [
      {
        displayName: 'Resource',
        name: 'resource',
        type: 'options',
        noDataExpression: true,
        options: [
          {
            name: 'Lead',
            value: 'lead',
          },
          {
            name: 'Demo Site',
            value: 'demoSite',
          },
          {
            name: 'Video',
            value: 'video',
          },
          {
            name: 'Email',
            value: 'email',
          },
          {
            name: 'Analytics',
            value: 'analytics',
          },
        ],
        default: 'lead',
      },

      // LEAD OPERATIONS
      {
        displayName: 'Operation',
        name: 'operation',
        type: 'options',
        noDataExpression: true,
        displayOptions: {
          show: {
            resource: ['lead'],
          },
        },
        options: [
          {
            name: 'Get',
            value: 'get',
            description: 'Get a lead by ID',
            action: 'Get a lead',
          },
          {
            name: 'Get All',
            value: 'getAll',
            description: 'Get all leads with filters',
            action: 'Get all leads',
          },
          {
            name: 'Update',
            value: 'update',
            description: 'Update a lead',
            action: 'Update a lead',
          },
          {
            name: 'Update Status',
            value: 'updateStatus',
            description: 'Update lead status',
            action: 'Update lead status',
          },
        ],
        default: 'getAll',
      },

      // Lead: Get operation
      {
        displayName: 'Lead ID',
        name: 'leadId',
        type: 'string',
        required: true,
        displayOptions: {
          show: {
            resource: ['lead'],
            operation: ['get', 'update', 'updateStatus'],
          },
        },
        default: '',
        description: 'The ID of the lead',
      },

      // Lead: Get All operation
      {
        displayName: 'Return All',
        name: 'returnAll',
        type: 'boolean',
        displayOptions: {
          show: {
            resource: ['lead'],
            operation: ['getAll'],
          },
        },
        default: false,
        description: 'Whether to return all results or only up to a given limit',
      },
      {
        displayName: 'Limit',
        name: 'limit',
        type: 'number',
        displayOptions: {
          show: {
            resource: ['lead'],
            operation: ['getAll'],
            returnAll: [false],
          },
        },
        typeOptions: {
          minValue: 1,
          maxValue: 100,
        },
        default: 50,
        description: 'Max number of results to return',
      },
      {
        displayName: 'Filters',
        name: 'filters',
        type: 'collection',
        placeholder: 'Add Filter',
        default: {},
        displayOptions: {
          show: {
            resource: ['lead'],
            operation: ['getAll'],
          },
        },
        options: [
          {
            displayName: 'Status',
            name: 'status',
            type: 'options',
            options: [
              { name: 'New', value: 'new' },
              { name: 'Pending Approval', value: 'pending_approval' },
              { name: 'Approved', value: 'approved' },
              { name: 'Rejected', value: 'rejected' },
              { name: 'Demo Generated', value: 'demo_generated' },
              { name: 'Video Created', value: 'video_created' },
              { name: 'Email Sent', value: 'email_sent' },
              { name: 'Contacted', value: 'contacted' },
            ],
            default: 'new',
          },
          {
            displayName: 'Category',
            name: 'category',
            type: 'string',
            default: '',
          },
          {
            displayName: 'Location',
            name: 'location',
            type: 'string',
            default: '',
          },
          {
            displayName: 'Min Score',
            name: 'min_score',
            type: 'number',
            default: 0,
            typeOptions: {
              minValue: 0,
              maxValue: 100,
            },
          },
        ],
      },

      // Lead: Update Status
      {
        displayName: 'Status',
        name: 'status',
        type: 'options',
        required: true,
        displayOptions: {
          show: {
            resource: ['lead'],
            operation: ['updateStatus'],
          },
        },
        options: [
          { name: 'Pending Approval', value: 'pending_approval' },
          { name: 'Approved', value: 'approved' },
          { name: 'Rejected', value: 'rejected' },
          { name: 'Demo Generated', value: 'demo_generated' },
          { name: 'Video Created', value: 'video_created' },
          { name: 'Email Sent', value: 'email_sent' },
          { name: 'Contacted', value: 'contacted' },
        ],
        default: 'approved',
      },

      // DEMO SITE OPERATIONS
      {
        displayName: 'Operation',
        name: 'operation',
        type: 'options',
        noDataExpression: true,
        displayOptions: {
          show: {
            resource: ['demoSite'],
          },
        },
        options: [
          {
            name: 'Create',
            value: 'create',
            description: 'Create a demo site',
            action: 'Create a demo site',
          },
          {
            name: 'Get',
            value: 'get',
            description: 'Get a demo site',
            action: 'Get a demo site',
          },
          {
            name: 'Get All',
            value: 'getAll',
            description: 'Get all demo sites',
            action: 'Get all demo sites',
          },
          {
            name: 'Deploy',
            value: 'deploy',
            description: 'Deploy a demo site',
            action: 'Deploy a demo site',
          },
        ],
        default: 'create',
      },

      // Demo Site: Create
      {
        displayName: 'Lead ID',
        name: 'leadId',
        type: 'string',
        required: true,
        displayOptions: {
          show: {
            resource: ['demoSite'],
            operation: ['create'],
          },
        },
        default: '',
        description: 'The ID of the lead to create demo site for',
      },
      {
        displayName: 'Business Name',
        name: 'businessName',
        type: 'string',
        required: true,
        displayOptions: {
          show: {
            resource: ['demoSite'],
            operation: ['create'],
          },
        },
        default: '',
        description: 'Name of the business',
      },
      {
        displayName: 'Industry',
        name: 'industry',
        type: 'string',
        required: true,
        displayOptions: {
          show: {
            resource: ['demoSite'],
            operation: ['create'],
          },
        },
        default: '',
        description: 'Industry/category of the business',
      },

      // Demo Site: Deploy
      {
        displayName: 'Demo Site ID',
        name: 'demoSiteId',
        type: 'string',
        required: true,
        displayOptions: {
          show: {
            resource: ['demoSite'],
            operation: ['get', 'deploy'],
          },
        },
        default: '',
        description: 'The ID of the demo site',
      },

      // VIDEO OPERATIONS
      {
        displayName: 'Operation',
        name: 'operation',
        type: 'options',
        noDataExpression: true,
        displayOptions: {
          show: {
            resource: ['video'],
          },
        },
        options: [
          {
            name: 'Create',
            value: 'create',
            description: 'Create a video',
            action: 'Create a video',
          },
          {
            name: 'Get',
            value: 'get',
            description: 'Get a video',
            action: 'Get a video',
          },
          {
            name: 'Get Status',
            value: 'getStatus',
            description: 'Get video generation status',
            action: 'Get video status',
          },
        ],
        default: 'create',
      },

      // Video: Create
      {
        displayName: 'Demo Site ID',
        name: 'demoSiteId',
        type: 'string',
        required: true,
        displayOptions: {
          show: {
            resource: ['video'],
            operation: ['create'],
          },
        },
        default: '',
        description: 'The ID of the demo site',
      },
      {
        displayName: 'Business Name',
        name: 'businessName',
        type: 'string',
        required: true,
        displayOptions: {
          show: {
            resource: ['video'],
            operation: ['create'],
          },
        },
        default: '',
        description: 'Name of the business',
      },

      // Video: Get
      {
        displayName: 'Video ID',
        name: 'videoId',
        type: 'string',
        required: true,
        displayOptions: {
          show: {
            resource: ['video'],
            operation: ['get', 'getStatus'],
          },
        },
        default: '',
        description: 'The ID of the video',
      },

      // EMAIL OPERATIONS
      {
        displayName: 'Operation',
        name: 'operation',
        type: 'options',
        noDataExpression: true,
        displayOptions: {
          show: {
            resource: ['email'],
          },
        },
        options: [
          {
            name: 'Send',
            value: 'send',
            description: 'Send an email',
            action: 'Send an email',
          },
        ],
        default: 'send',
      },

      // Email: Send
      {
        displayName: 'Lead ID',
        name: 'leadId',
        type: 'string',
        required: true,
        displayOptions: {
          show: {
            resource: ['email'],
            operation: ['send'],
          },
        },
        default: '',
        description: 'The ID of the lead',
      },
      {
        displayName: 'Demo URL',
        name: 'demoUrl',
        type: 'string',
        required: true,
        displayOptions: {
          show: {
            resource: ['email'],
            operation: ['send'],
          },
        },
        default: '',
        description: 'URL of the demo site',
      },
      {
        displayName: 'Video URL',
        name: 'videoUrl',
        type: 'string',
        displayOptions: {
          show: {
            resource: ['email'],
            operation: ['send'],
          },
        },
        default: '',
        description: 'URL of the video (optional)',
      },

      // ANALYTICS OPERATIONS
      {
        displayName: 'Operation',
        name: 'operation',
        type: 'options',
        noDataExpression: true,
        displayOptions: {
          show: {
            resource: ['analytics'],
          },
        },
        options: [
          {
            name: 'Get Overview',
            value: 'getOverview',
            description: 'Get analytics overview',
            action: 'Get analytics overview',
          },
          {
            name: 'Get Conversion Stats',
            value: 'getConversionStats',
            description: 'Get conversion statistics',
            action: 'Get conversion stats',
          },
        ],
        default: 'getOverview',
      },
    ],
  };

  async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
    const items = this.getInputData();
    const returnData: INodeExecutionData[] = [];
    const resource = this.getNodeParameter('resource', 0) as string;
    const operation = this.getNodeParameter('operation', 0) as string;

    const credentials = await this.getCredentials('craigleadsProApi');
    const apiUrl = credentials.apiUrl as string;
    const apiKey = credentials.apiKey as string;

    for (let i = 0; i < items.length; i++) {
      try {
        let responseData;

        // LEAD RESOURCE
        if (resource === 'lead') {
          if (operation === 'get') {
            const leadId = this.getNodeParameter('leadId', i) as string;
            const options: OptionsWithUri = {
              method: 'GET',
              uri: `${apiUrl}/api/v1/leads/${leadId}`,
              headers: {
                'Authorization': `Bearer ${apiKey}`,
              },
              json: true,
            };
            responseData = await this.helpers.request(options);
          } else if (operation === 'getAll') {
            const returnAll = this.getNodeParameter('returnAll', i) as boolean;
            const filters = this.getNodeParameter('filters', i, {}) as any;

            const qs: any = {};
            if (!returnAll) {
              qs.limit = this.getNodeParameter('limit', i) as number;
            }
            if (filters.status) qs.status = filters.status;
            if (filters.category) qs.category = filters.category;
            if (filters.location) qs.location = filters.location;
            if (filters.min_score) qs.min_score = filters.min_score;

            const options: OptionsWithUri = {
              method: 'GET',
              uri: `${apiUrl}/api/v1/leads`,
              qs,
              headers: {
                'Authorization': `Bearer ${apiKey}`,
              },
              json: true,
            };
            responseData = await this.helpers.request(options);
          } else if (operation === 'updateStatus') {
            const leadId = this.getNodeParameter('leadId', i) as string;
            const status = this.getNodeParameter('status', i) as string;

            const options: OptionsWithUri = {
              method: 'PATCH',
              uri: `${apiUrl}/api/v1/leads/${leadId}/status`,
              body: { status },
              headers: {
                'Authorization': `Bearer ${apiKey}`,
              },
              json: true,
            };
            responseData = await this.helpers.request(options);
          }
        }

        // DEMO SITE RESOURCE
        else if (resource === 'demoSite') {
          if (operation === 'create') {
            const leadId = this.getNodeParameter('leadId', i) as string;
            const businessName = this.getNodeParameter('businessName', i) as string;
            const industry = this.getNodeParameter('industry', i) as string;

            const options: OptionsWithUri = {
              method: 'POST',
              uri: `${apiUrl}/api/v1/phase3/demo-sites`,
              body: {
                lead_id: leadId,
                business_name: businessName,
                industry,
              },
              headers: {
                'Authorization': `Bearer ${apiKey}`,
              },
              json: true,
            };
            responseData = await this.helpers.request(options);
          } else if (operation === 'get') {
            const demoSiteId = this.getNodeParameter('demoSiteId', i) as string;
            const options: OptionsWithUri = {
              method: 'GET',
              uri: `${apiUrl}/api/v1/phase3/demo-sites/${demoSiteId}`,
              headers: {
                'Authorization': `Bearer ${apiKey}`,
              },
              json: true,
            };
            responseData = await this.helpers.request(options);
          } else if (operation === 'deploy') {
            const demoSiteId = this.getNodeParameter('demoSiteId', i) as string;
            const options: OptionsWithUri = {
              method: 'POST',
              uri: `${apiUrl}/api/v1/phase3/demo-sites/${demoSiteId}/deploy`,
              headers: {
                'Authorization': `Bearer ${apiKey}`,
              },
              json: true,
            };
            responseData = await this.helpers.request(options);
          }
        }

        // VIDEO RESOURCE
        else if (resource === 'video') {
          if (operation === 'create') {
            const demoSiteId = this.getNodeParameter('demoSiteId', i) as string;
            const businessName = this.getNodeParameter('businessName', i) as string;

            const options: OptionsWithUri = {
              method: 'POST',
              uri: `${apiUrl}/api/v1/videos/create`,
              body: {
                demo_site_id: demoSiteId,
                business_name: businessName,
              },
              headers: {
                'Authorization': `Bearer ${apiKey}`,
              },
              json: true,
            };
            responseData = await this.helpers.request(options);
          } else if (operation === 'get') {
            const videoId = this.getNodeParameter('videoId', i) as string;
            const options: OptionsWithUri = {
              method: 'GET',
              uri: `${apiUrl}/api/v1/videos/${videoId}`,
              headers: {
                'Authorization': `Bearer ${apiKey}`,
              },
              json: true,
            };
            responseData = await this.helpers.request(options);
          } else if (operation === 'getStatus') {
            const videoId = this.getNodeParameter('videoId', i) as string;
            const options: OptionsWithUri = {
              method: 'GET',
              uri: `${apiUrl}/api/v1/videos/${videoId}/status`,
              headers: {
                'Authorization': `Bearer ${apiKey}`,
              },
              json: true,
            };
            responseData = await this.helpers.request(options);
          }
        }

        // EMAIL RESOURCE
        else if (resource === 'email') {
          if (operation === 'send') {
            const leadId = this.getNodeParameter('leadId', i) as string;
            const demoUrl = this.getNodeParameter('demoUrl', i) as string;
            const videoUrl = this.getNodeParameter('videoUrl', i, '') as string;

            const options: OptionsWithUri = {
              method: 'POST',
              uri: `${apiUrl}/api/v1/emails/send`,
              body: {
                lead_id: leadId,
                demo_url: demoUrl,
                video_url: videoUrl,
              },
              headers: {
                'Authorization': `Bearer ${apiKey}`,
              },
              json: true,
            };
            responseData = await this.helpers.request(options);
          }
        }

        // ANALYTICS RESOURCE
        else if (resource === 'analytics') {
          if (operation === 'getOverview') {
            const options: OptionsWithUri = {
              method: 'GET',
              uri: `${apiUrl}/api/v1/analytics/overview`,
              headers: {
                'Authorization': `Bearer ${apiKey}`,
              },
              json: true,
            };
            responseData = await this.helpers.request(options);
          } else if (operation === 'getConversionStats') {
            const options: OptionsWithUri = {
              method: 'GET',
              uri: `${apiUrl}/api/v1/analytics/conversions`,
              headers: {
                'Authorization': `Bearer ${apiKey}`,
              },
              json: true,
            };
            responseData = await this.helpers.request(options);
          }
        }

        returnData.push({
          json: responseData,
          pairedItem: { item: i },
        });
      } catch (error) {
        if (this.continueOnFail()) {
          returnData.push({
            json: { error: error.message },
            pairedItem: { item: i },
          });
          continue;
        }
        throw error;
      }
    }

    return [returnData];
  }
}
