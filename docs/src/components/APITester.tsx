import React, { useState, useCallback } from 'react';
import { useColorMode } from '@docusaurus/theme-common';
import styles from './APITester.module.css';

interface APITesterProps {
  baseUrl?: string;
  height?: string;
}

interface RequestConfig {
  method: string;
  url: string;
  headers: Record<string, string>;
  body: string;
  params: Record<string, string>;
}

interface ResponseData {
  status: number;
  statusText: string;
  headers: Record<string, string>;
  data: any;
  time: number;
}

const APITester: React.FC<APITesterProps> = ({ 
  baseUrl = 'https://saathiiapp.com',
  height = '600px'
}) => {
  const { colorMode } = useColorMode();
  const [request, setRequest] = useState<RequestConfig>({
    method: 'GET',
    url: '',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': ''
    },
    body: '',
    params: {}
  });

  const [response, setResponse] = useState<ResponseData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'];

  const handleMethodChange = (method: string) => {
    setRequest(prev => ({ ...prev, method }));
  };

  const handleUrlChange = (url: string) => {
    setRequest(prev => ({ ...prev, url }));
  };

  const handleHeaderChange = (key: string, value: string) => {
    setRequest(prev => ({
      ...prev,
      headers: { ...prev.headers, [key]: value }
    }));
  };

  const addHeader = () => {
    setRequest(prev => ({
      ...prev,
      headers: { ...prev.headers, '': '' }
    }));
  };

  const removeHeader = (key: string) => {
    setRequest(prev => {
      const newHeaders = { ...prev.headers };
      delete newHeaders[key];
      return { ...prev, headers: newHeaders };
    });
  };

  const handleBodyChange = (body: string) => {
    setRequest(prev => ({ ...prev, body }));
  };

  const handleParamChange = (key: string, value: string) => {
    setRequest(prev => ({
      ...prev,
      params: { ...prev.params, [key]: value }
    }));
  };

  const addParam = () => {
    setRequest(prev => ({
      ...prev,
      params: { ...prev.params, '': '' }
    }));
  };

  const removeParam = (key: string) => {
    setRequest(prev => {
      const newParams = { ...prev.params };
      delete newParams[key];
      return { ...prev, params: newParams };
    });
  };

  const buildUrl = () => {
    let url = baseUrl + request.url;
    const params = Object.entries(request.params).filter(([k, v]) => k && v);
    if (params.length > 0) {
      const searchParams = new URLSearchParams(params);
      url += '?' + searchParams.toString();
    }
    return url;
  };

  const sendRequest = useCallback(async () => {
    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const url = buildUrl();
      const startTime = Date.now();

      const headers: Record<string, string> = {};
      Object.entries(request.headers).forEach(([key, value]) => {
        if (key && value) {
          headers[key] = value;
        }
      });

      const fetchOptions: RequestInit = {
        method: request.method,
        headers
      };

      if (['POST', 'PUT', 'PATCH'].includes(request.method) && request.body) {
        fetchOptions.body = request.body;
      }

      const res = await fetch(url, fetchOptions);
      const endTime = Date.now();

      const responseHeaders: Record<string, string> = {};
      res.headers.forEach((value, key) => {
        responseHeaders[key] = value;
      });

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
        headers: responseHeaders,
        data: responseData,
        time: endTime - startTime
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed');
    } finally {
      setLoading(false);
    }
  }, [request, baseUrl]);

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
    <div className={`${styles.apiTester} ${colorMode === 'dark' ? styles.dark : styles.light}`} style={{ height }}>
      <div className={styles.container}>
        {/* Request Section */}
        <div className={styles.requestSection}>
          <div className={styles.requestHeader}>
            <h3>Request</h3>
            <button 
              className={styles.sendButton} 
              onClick={sendRequest}
              disabled={loading}
            >
              {loading ? 'Sending...' : 'Send'}
            </button>
          </div>

          {/* Method and URL */}
          <div className={styles.methodUrlRow}>
            <select 
              value={request.method} 
              onChange={(e) => handleMethodChange(e.target.value)}
              className={styles.methodSelect}
            >
              {methods.map(method => (
                <option key={method} value={method}>{method}</option>
              ))}
            </select>
            <input
              type="text"
              value={request.url}
              onChange={(e) => handleUrlChange(e.target.value)}
              placeholder="/auth/request_otp"
              className={styles.urlInput}
            />
          </div>

          {/* Params */}
          <div className={styles.section}>
            <div className={styles.sectionHeader}>
              <h4>Query Parameters</h4>
              <button onClick={addParam} className={styles.addButton}>+ Add</button>
            </div>
            {Object.entries(request.params).map(([key, value], index) => (
              <div key={index} className={styles.keyValueRow}>
                <input
                  type="text"
                  value={key}
                  onChange={(e) => handleParamChange(e.target.value, value)}
                  placeholder="Key"
                  className={styles.keyInput}
                />
                <input
                  type="text"
                  value={value}
                  onChange={(e) => handleParamChange(key, e.target.value)}
                  placeholder="Value"
                  className={styles.valueInput}
                />
                <button 
                  onClick={() => removeParam(key)}
                  className={styles.removeButton}
                >
                  ×
                </button>
              </div>
            ))}
          </div>

          {/* Headers */}
          <div className={styles.section}>
            <div className={styles.sectionHeader}>
              <h4>Headers</h4>
              <button onClick={addHeader} className={styles.addButton}>+ Add</button>
            </div>
            {Object.entries(request.headers).map(([key, value], index) => (
              <div key={index} className={styles.keyValueRow}>
                <input
                  type="text"
                  value={key}
                  onChange={(e) => handleHeaderChange(e.target.value, value)}
                  placeholder="Header name"
                  className={styles.keyInput}
                />
                <input
                  type="text"
                  value={value}
                  onChange={(e) => handleHeaderChange(key, e.target.value)}
                  placeholder="Header value"
                  className={styles.valueInput}
                />
                <button 
                  onClick={() => removeHeader(key)}
                  className={styles.removeButton}
                >
                  ×
                </button>
              </div>
            ))}
          </div>

          {/* Body */}
          {['POST', 'PUT', 'PATCH'].includes(request.method) && (
            <div className={styles.section}>
              <h4>Body</h4>
              <textarea
                value={request.body}
                onChange={(e) => handleBodyChange(e.target.value)}
                placeholder='{"phone": "+919876543210"}'
                className={styles.bodyTextarea}
                rows={8}
              />
            </div>
          )}
        </div>

        {/* Response Section */}
        <div className={styles.responseSection}>
          <h3>Response</h3>
          
          {error && (
            <div className={styles.error}>
              <strong>Error:</strong> {error}
            </div>
          )}

          {response && (
            <>
              <div className={styles.responseHeader}>
                <span 
                  className={styles.statusCode}
                  style={{ color: getStatusColor(response.status) }}
                >
                  {response.status} {response.statusText}
                </span>
                <span className={styles.responseTime}>{response.time}ms</span>
              </div>

              <div className={styles.responseTabs}>
                <div className={styles.tabContent}>
                  <h4>Response Body</h4>
                  <pre className={styles.responseBody}>
                    {formatJson(response.data)}
                  </pre>
                </div>
              </div>
            </>
          )}

          {!response && !error && !loading && (
            <div className={styles.placeholder}>
              Click "Send" to make a request
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default APITester;
