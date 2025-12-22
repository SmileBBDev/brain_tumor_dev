import React from 'react';
import ReactDom from 'react-dom/client';
import {QueryClient, QueryClientProvider} from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import App from './app/App';


// React Query 세팅
const queryClient = new QueryClient();

ReactDom.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App/>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
);