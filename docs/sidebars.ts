import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */
const sidebars: SidebarsConfig = {
  // API Documentation Sidebar
  apiSidebar: [
    'getting-started',
    {
      type: 'category',
      label: 'API Reference',
      items: [
        'api/authentication',
        'api/user-management',
        'api/presence-status',
        'api/feeds',
        'api/wallets',
        'api/call-management',
        'api/favorites',
        'api/blocking',
        'api/reporting',
        'api/verification',
        'api/listener-verification',
        'api/help-support',
        // 'api/websocket-realtime', // removed
        'api/database-impact',
        'api/swagger-ui',
      ],
    },
    // Background tasks removed - functionality integrated into main API
  ],

};

export default sidebars;
