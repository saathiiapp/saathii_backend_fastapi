import { useEffect } from 'react';
import { Redirect } from '@docusaurus/router';

export default function Home() {
  // Redirect to the getting started documentation
  return <Redirect to="/docs/getting-started" />;
}
