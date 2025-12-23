import React from 'react';
import ReactDom from 'react-dom/client';
import {QueryClient, QueryClientProvider} from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import App from './app/App';
import '@/assets/style/variables.css'; // CSS 변수
import '@/assets/style/cdssCommonStyle.css'; // 공통 스타일 적용
import '@/assets/style/layout.css'; // 레이아웃 스타일 적용
import '@fortawesome/fontawesome-free/css/all.min.css'; // FontAwesome 아이콘 스타일

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