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
        'api/verification',
        'api/websocket-realtime',
        'api/database-impact',
        'api/swagger-ui',
      ],
    },
    {
      type: 'category',
      label: 'Background Tasks',
      items: [
        'background_tasks/index',
        'background_tasks/background-tasks',
        'background_tasks/background-tasks-api',
        'background_tasks/background-tasks-summary',
      ],
    },
  ],

  // Guides Sidebar
  guidesSidebar: [
    {
      type: 'category',
      label: 'Getting Started',
      items: [
        'guides/installation',
        'guides/s3-setup',
        'guides/background-tasks-setup',
      ],
    },
    {
      type: 'category',
      label: 'React Native Integration',
      items: [
        'guides/react-native-authentication',
        'guides/react-native-user-management',
        'guides/react-native-wallets',
        'guides/react-native-calls',
        'guides/react-native-feeds',
        'guides/react-native-favorites',
        'guides/react-native-blocking',
        'guides/react-native-websocket',
      ],
    },
  ],
};

export default sidebars;
