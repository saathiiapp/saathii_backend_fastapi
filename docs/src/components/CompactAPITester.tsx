import React, { useState, useCallback } from 'react';
import { useColorMode } from '@docusaurus/theme-common';
import styles from './CompactAPITester.module.css';

interface CompactAPITesterProps {
  endpoint: string;
  method?: string;
  description?: string;
  exampleBody?: string;
  baseUrl?: string;
}

const CompactAPITester: React.FC<CompactAPITesterProps> = ({
  endpoint,
  method = 'GET',
  description = '',
  exampleBody = '',
  baseUrl = 'https://saathiiapp.com'
}) => {
  const { colorMode } = useColorMode();
  const [isExpanded, setIsExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [requestBody, setRequestBody] = useState(exampleBody);
  const [authToken, setAuthToken] = useState('');

  const sendRequest = useCallback(async () => {
    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const url = `${baseUrl}${endpoint}`;
      const startTime = Date.now();

      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      };

      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const fetchOptions: RequestInit = {
        method,
        headers
      };

      if (['POST', 'PUT', 'PATCH'].includes(method) && requestBody) {
        fetchOptions.body = requestBody;
      }

      const res = await fetch(url, fetchOptions);
      const endTime = Date.now();

      let responseData;
      const contentType = res.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        responseData = await res.json();
      } else {
        responseData = await res.text();
      }

      setResponse({
        status: res.status,
        statusText: res.statusText,
        data: responseData,
        time: endTime - startTime
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed');
    } finally {
      setLoading(false);
    }
  }, [endpoint, method, requestBody, authToken, baseUrl]);

  const formatJson = (obj: any) => {
    try {
      return JSON.stringify(obj, null, 2);
    } catch {
      return String(obj);
    }
  };

  const getStatusColor = (status: number) => {
    if (status >= 200 && status < 300) return '#28a745';
    if (status >= 300 && status < 400) return '#ffc107';
    if (status >= 400 && status < 500) return '#fd7e14';
    if (status >= 500) return '#dc3545';
    return '#6c757d';
  };

  return (
    <div className={`${styles.compactTester} ${colorMode === 'dark' ? styles.dark : styles.light}`}>
      <div className={styles.header}>
        <div className={styles.endpointInfo}>
          <span className={styles.method}>{method}</span>
          <span className={styles.endpoint}>{endpoint}</span>
          {description && <span className={styles.description}>{description}</span>}
        </div>
        <button 
          className={styles.toggleButton}
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? 'Hide' : 'Test'}
        </button>
      </div>

      {isExpanded && (
        <div className={styles.content}>
          <div className={styles.inputs}>
            {['POST', 'PUT', 'PATCH'].includes(method) && (
              <div className={styles.inputGroup}>
                <label>Request Body:</label>
                <textarea
                  value={requestBody}
                  onChange={(e) => setRequestBody(e.target.value)}
                  placeholder="Enter JSON request body..."
                  className={styles.bodyInput}
                  rows={4}
                />
              </div>
            )}
            
            <div className={styles.inputGroup}>
              <label>Authorization Token (optional):</label>
              <input
                type="text"
                value={authToken}
                onChange={(e) => setAuthToken(e.target.value)}
                placeholder="Enter Bearer token..."
                className={styles.tokenInput}
              />
            </div>

            <button 
              className={styles.sendButton}
              onClick={sendRequest}
              disabled={loading}
            >
              {loading ? 'Sending...' : 'Send Request'}
            </button>
          </div>

          {error && (
            <div className={styles.error}>
              <strong>Error:</strong> {error}
            </div>
          )}

          {response && (
            <div className={styles.response}>
              <div className={styles.responseHeader}>
                <span 
                  className={styles.statusCode}
                  style={{ color: getStatusColor(response.status) }}
                >
                  {response.status} {response.statusText}
                </span>
                <span className={styles.responseTime}>{response.time}ms</span>
              </div>
              <pre className={styles.responseBody}>
                {formatJson(response.data)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default CompactAPITester;
