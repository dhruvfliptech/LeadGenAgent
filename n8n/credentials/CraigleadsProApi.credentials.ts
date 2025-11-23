import {
  IAuthenticateGeneric,
  ICredentialTestRequest,
  ICredentialType,
  INodeProperties,
} from 'n8n-workflow';

export class CraigleadsProApi implements ICredentialType {
  name = 'craigleadsProApi';
  displayName = 'CraigLeads Pro API';
  documentationUrl = 'https://docs.craigleadspro.com/api';
  properties: INodeProperties[] = [
    {
      displayName: 'API URL',
      name: 'apiUrl',
      type: 'string',
      default: 'http://localhost:8000',
      description: 'Base URL for the CraigLeads Pro API',
      placeholder: 'https://api.craigleadspro.com',
    },
    {
      displayName: 'API Key',
      name: 'apiKey',
      type: 'string',
      typeOptions: {
        password: true,
      },
      default: '',
      required: true,
      description: 'API key for authentication',
    },
    {
      displayName: 'Timeout',
      name: 'timeout',
      type: 'number',
      default: 30000,
      description: 'Request timeout in milliseconds',
    },
  ];

  // This allows the credential to be used by other nodes
  authenticate: IAuthenticateGeneric = {
    type: 'generic',
    properties: {
      headers: {
        Authorization: '=Bearer {{$credentials.apiKey}}',
      },
    },
  };

  // Test the credential
  test: ICredentialTestRequest = {
    request: {
      baseURL: '={{$credentials.apiUrl}}',
      url: '/api/v1/health',
      method: 'GET',
    },
  };
}
