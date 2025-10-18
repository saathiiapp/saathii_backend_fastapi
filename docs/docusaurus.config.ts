import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

const config: Config = {
  title: 'Saathii Backend API',
  tagline: 'Because being heard changes everything.',
  favicon: 'img/favicon.ico',

  // Future flags for improved compatibility
  future: {
    v4: true, // Improve compatibility with upcoming versions
  },

  // Set the production url of your site here
  url: 'https://docs.saathiiapp.com',
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: '/',

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: 'saathii', // Usually your GitHub org/user name.
  projectName: 'saathii-backend-api', // Usually your repo name.

  onBrokenLinks: 'warn',

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          editUrl:
            'https://github.com/saathii/saathii-backend-api/tree/main/docs/',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    // Replace with your project's social card
    image: 'img/logo.png',
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'Saathii API',
      logo: {
        alt: 'Saathii Logo',
        src: 'img/logo.png',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'apiSidebar',
          position: 'left',
          label: 'API Documentation',
        },
        {
          href: 'https://saathiiapp.com/docs',
          label: 'Swagger UI',
          position: 'right',
        },
        {
          href: 'https://saathiiapp.com/redoc',
          label: 'ReDoc',
          position: 'right',
        },
        {
          href: 'https://github.com/saathii/saathii-backend-api',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'API Documentation',
          items: [
            {
              label: 'Getting Started',
              to: '/docs/getting-started',
            },
            {
              label: 'Authentication',
              to: '/docs/api/authentication',
            },
            {
              label: 'User Management',
              to: '/docs/api/user-management',
            },
            {
              label: 'Call Management',
              to: '/docs/api/call-management',
            },
          ],
        },
        {
          title: 'Resources',
          items: [
            {
              label: 'Swagger UI',
              href: 'https://saathiiapp.com/docs',
            },
            {
              label: 'ReDoc',
              href: 'https://saathiiapp.com/redoc',
            },
          ],
        },
        {
          title: 'Community',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/saathii/saathii-backend-api',
            },
            {
              label: 'Issues',
              href: 'https://github.com/saathii/saathii-backend-api/issues',
            },
            {
              label: 'Discussions',
              href: 'https://github.com/saathii/saathii-backend-api/discussions',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Saathii. All rights reserved.`,
      links: [
        {
          title: 'Mission',
          items: [
            {
              label: 'Because being heard changes everything.',
              to: '/docs/intro',
            },
          ],
        },
      ],
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
