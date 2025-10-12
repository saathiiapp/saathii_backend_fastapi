import React, { useState } from 'react';
import { useColorMode } from '@docusaurus/theme-common';

interface SwaggerUIProps {
  url?: string;
  height?: string;
}

const SwaggerUI: React.FC<SwaggerUIProps> = ({ 
  url = 'https://saathiiapp.com/openapi.json',
  height = '600px'
}) => {
  const { colorMode } = useColorMode();
  const [isLoading, setIsLoading] = useState(true);

  // Create a simple HTML page with Swagger UI
  const swaggerHTML = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>Saathii API Documentation</title>
      <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css" />
      <style>
        body { margin: 0; padding: 0; }
        .swagger-ui .topbar { display: none; }
        .swagger-ui .info { margin: 20px 0; }
        .swagger-ui .scheme-container { background: #fafafa; padding: 10px; margin: 10px 0; }
      </style>
    </head>
    <body>
      <div id="swagger-ui"></div>
      <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js"></script>
      <script>
        window.onload = function() {
          SwaggerUIBundle({
            url: '${url}',
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [
              SwaggerUIBundle.presets.apis,
              SwaggerUIBundle.presets.standalone
            ],
            layout: "StandaloneLayout",
            tryItOutEnabled: true,
            requestInterceptor: function(request) {
              // Add CORS headers
              request.headers['Access-Control-Allow-Origin'] = '*';
              request.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS';
              request.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization';
              return request;
            },
            responseInterceptor: function(response) {
              return response;
            }
          });
        };
      </script>
    </body>
    </html>
  `;

  const dataUrl = `data:text/html;charset=utf-8,${encodeURIComponent(swaggerHTML)}`;

  return (
    <div style={{ width: '100%', height, border: '1px solid #e1e4e8', borderRadius: '6px', overflow: 'hidden', position: 'relative' }}>
      {isLoading && (
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          textAlign: 'center',
          zIndex: 1
        }}>
          <div style={{ marginBottom: '10px' }}>Loading API Explorer...</div>
          <div style={{ 
            width: '40px', 
            height: '40px', 
            border: '4px solid #f3f3f3',
            borderTop: '4px solid #0366d6',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto'
          }}></div>
          <style>{`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}</style>
        </div>
      )}
      <iframe
        src={dataUrl}
        style={{ 
          width: '100%', 
          height: '100%', 
          border: 'none',
          opacity: isLoading ? 0 : 1,
          transition: 'opacity 0.3s ease'
        }}
        title="Swagger UI"
        onLoad={() => setIsLoading(false)}
        sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-top-navigation"
      />
      <div style={{
        position: 'absolute',
        top: '10px',
        right: '10px',
        zIndex: 2
      }}>
        <a 
          href="https://saathiiapp.com/docs" 
          target="_blank" 
          rel="noopener noreferrer"
          style={{
            padding: '6px 12px',
            backgroundColor: '#0366d6',
            color: 'white',
            textDecoration: 'none',
            borderRadius: '4px',
            fontSize: '12px',
            marginRight: '8px'
          }}
        >
          Open in New Tab
        </a>
        <a 
          href="https://saathiiapp.com/redoc" 
          target="_blank" 
          rel="noopener noreferrer"
          style={{
            padding: '6px 12px',
            backgroundColor: '#28a745',
            color: 'white',
            textDecoration: 'none',
            borderRadius: '4px',
            fontSize: '12px'
          }}
        >
          ReDoc
        </a>
      </div>
    </div>
  );
};

export default SwaggerUI;
