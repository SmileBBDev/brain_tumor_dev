<h2>프로젝트 소개</h2>

이 프로젝트는 React(Vite) 프론트엔드 + Django 백엔드 구조로 이뤄져 있습니다.

병원용 대시보드 / 권한 기반 메뉴 / 실시간(WebSocket) 기능이 동작하고 있습니다.

<br/>
<br/>

<h2> 🖥️ 프론트엔드 (brain_tumor_front)</h2>
<h3>요약</h3>
  
1.사용자가 보는 화면(UI)

2.로그인 후 역할(Role)에 따라 메뉴/페이지 다르게 표시

3.백엔드 API + WebSocket 연결

<span></span>

<h3>📂 주요 파일/폴더 구조 설명</h3>
<h4>최상위</h4>

index.html : 화면의 뼈대 (React가 붙는 자리)

package.json : 필요한 프로그램 목록

vite.config.ts : 개발 서버 설정

<h4> 폴더 구조 </h4>
src/

-------------------------------------------------------
경로	  &nbsp; &nbsp; | &nbsp; &nbsp;  역할
-------------------------------------------------------
main.tsx		  	    	  &nbsp; &nbsp;    | &nbsp; &nbsp; React 시작 지점 (가장 먼저 실행) <br/>
app/App.tsx		   	    	&nbsp; &nbsp;    | &nbsp; &nbsp; 전체 화면 레이아웃, 로그인 여부 판단 <br/>
app/HomeRedirect.tsx		&nbsp; &nbsp;    | &nbsp; &nbsp; 로그인 후 첫 페이지 이동 로직 <br/>
router/		    	    	  &nbsp; &nbsp;    | &nbsp; &nbsp; 페이지 주소(URL) 관리 <br/>
router/routeMap.tsx		  &nbsp; &nbsp;    | &nbsp; &nbsp; 권한별 접근 가능한 페이지 정의 <br/>
router/AppRoutes.tsx		&nbsp; &nbsp;    | &nbsp; &nbsp; 실제 React Route 설정 <br/>
services/api.ts		    	&nbsp; &nbsp;    | &nbsp; &nbsp; 백엔드 API 호출 함수 모음 <br/>
socket/permissionSocket.ts &nbsp; &nbsp; | &nbsp; &nbsp; 권한 변경 실시간 수신(WebSocket) <br/>
types/menu.ts		    	  &nbsp; &nbsp;    | &nbsp; &nbsp; 메뉴/권한 타입 정의 <br/>
assets/		    	    	  &nbsp; &nbsp;    | &nbsp; &nbsp; 이미지, CSS <br/>


<h4>중요 포인트</h4>
메뉴 하드코딩 ❌ → routeMap.tsx + 서버 데이터 기반

권한 바뀌면 Sidebar 즉시 변경 (WebSocket)

<br/>
<br/>

<h2> 🖥️ 백엔드 (brain_tumor_back)</h2>
<h3>요약</h3>

1. 로그인 / 권한 / 메뉴 데이터 제공

2. WebSocket 서버

3. API 제공



<h3>📂 주요 파일/폴더 구조 설명</h3능
