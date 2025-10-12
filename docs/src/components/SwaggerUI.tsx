import React, { useEffect, useRef } from 'react';
import { useColorMode } from '@docusaurus/theme-common';

interface SwaggerUIProps {
  url?: string;
  height?: string;
}

const SwaggerUI: React.FC<SwaggerUIProps> = ({ 
  url = 'https://saathiiapp.com/docs',
  height = '600px'
}) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const { colorMode } = useColorMode();

  useEffect(() => {
    if (iframeRef.current) {
      // Add theme parameter based on color mode
      const themeParam = colorMode === 'dark' ? '&theme=dark' : '';
      const fullUrl = `${url}${themeParam}`;
      iframeRef.current.src = fullUrl;
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
