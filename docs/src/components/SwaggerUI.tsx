import React, { useEffect, useRef } from 'react';
import { useColorMode } from '@docusaurus/theme-common';

interface SwaggerUIProps {
  url?: string;
  height?: string;
}

const SwaggerUI: React.FC<SwaggerUIProps> = ({ 
  url = 'https://saathiiapp.com/openapi.json',
  height = '600px'
}) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const { colorMode } = useColorMode();

  useEffect(() => {
    if (iframeRef.current) {
      // Create Swagger UI URL with the OpenAPI JSON schema
      const swaggerUIUrl = `https://petstore.swagger.io/?url=${encodeURIComponent(url)}`;
      iframeRef.current.src = swaggerUIUrl;
    }
  }, [url, colorMode]);

  return (
    <div style={{ width: '100%', height, border: '1px solid #e1e4e8', borderRadius: '6px', overflow: 'hidden' }}>
      <iframe
        ref={iframeRef}
        style={{ width: '100%', height: '100%', border: 'none' }}
        title="Swagger UI"
        sandbox="allow-scripts allow-same-origin allow-forms"
      />
    </div>
  );
};

export default SwaggerUI;
