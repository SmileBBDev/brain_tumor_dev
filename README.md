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



<h3>📂 주요 파일/폴더 구조 설명</h3>
1.manage.py : 서버 실행 버튼 같은 파일

2.config/

-------------------------------------------------------
파일	  &nbsp; &nbsp; | &nbsp; &nbsp;  역할
-------------------------------------------------------
settings.py	 &nbsp; &nbsp;    | &nbsp; &nbsp;  공통 설정 <br/>
dev.py	 &nbsp; &nbsp;    | &nbsp; &nbsp;  개발용 설정 <br/>
prod.py	 &nbsp; &nbsp;    | &nbsp; &nbsp;  배포용 설정 <br/>
urls.py	 &nbsp; &nbsp;    | &nbsp; &nbsp;  API 주소 목록 <br/>
asgi.py  &nbsp; &nbsp;    | &nbsp; &nbsp;  WebSocket 연결 담당 <br/>

3.apps/ : 실제 기능들이 들어있는 곳

-------------------------------------------------------
앱 &nbsp; &nbsp; | &nbsp; &nbsp;  역할
-------------------------------------------------------

accounts	&nbsp; &nbsp;    | &nbsp; &nbsp;  로그인 / 사용자 <br/>
roles	 &nbsp; &nbsp;    | &nbsp; &nbsp;  역할(Role) <br/>
menus	 &nbsp; &nbsp;    | &nbsp; &nbsp;  메뉴 정보 <br/>
permissions	&nbsp; &nbsp;    | &nbsp; &nbsp;  권한 관리 <br/>


<br/>
<br/>

<h2> 세팅 방법 </h2>
<h3>1단계: 프로그램 설치</h3>
Node.js 설치 (프론트용)

Python 3.10 이상 설치

<h3>2단계: 프론트 실행</h3>
cd front_code <br/>
npm install <br/>
npm run dev <br/>

* 브라우저에서 http://localhost:5173 접속 -> 로그인 화면 호출됨

<h3>3단계: 백엔드 실행</h3>
cd back_code <br/>
python -m venv venv <br/>
venv\Scripts\activate <br/>
pip install -r requirements.txt <br/>
daphne -b 127.0.0.1 -p 8000 config.asgi:application

* 실행성공 :  http://localhost:8000
