/* Editable SVG motion design. Schematic NAV1 schedule; no model is executed. */
(function(root){
'use strict';
const W=1600,H=900,D=168;
const P={ink:'#173846',muted:'#657D86',blue:'#337ACB',gold:'#D99A45',green:'#159B80',purple:'#9276C7',red:'#D46D6A',paper:'#F8FAF9',line:'#D9E3E5'};
const phases=[[0,18,'THE GEOMETRY OF A PLAN'],[18,58,'ENDPOINT FEEDBACK'],[58,88,'A SHARED CENTER'],[88,116,'LOCAL REFINEMENT'],[116,142,'FUSION & COMPARISON'],[142,168,'THE COMPLETE MOTION']];
const caps=[
[0,7,'A trajectory is a sequence of vehicle poses, not just a line on the road.'],
[7,12,'In a narrow passage, a small lateral change alters the remaining clearance.'],
[12,18,'Longitudinal changes alter the gap to the vehicle ahead at the same timestamp.'],
[18,25,'Start with an endpoint request. A native parent supplies the path in between.'],
[25,33,'Score the complete path, then store its utility at the terminal state it reaches.'],
[33,43,'Feedback from nearby reached states guides the next completion requests.'],
[43,51,'The archive uses position, heading and speed. Here we see its XY projection.'],
[51,58,'Each new request becomes a complete path before its utility enters the archive.'],
[58,67,'The accepted endpoint plan meets a native proposal from the second planner.'],
[67,77,'Bounded interpolation and geometric search establish a shared trajectory center.'],
[77,88,'Longitudinal, lateral and timing adjustments refine the motion around this center.'],
[88,98,'One branch tests bounded blends with proposals from both frozen planners.'],
[98,108,'The control branch adds the bounded difference between two rollouts to the center.'],
[108,116,'Both branches start from the same center. Zero control change preserves it exactly.'],
[116,125,'Align the proposal and control trajectories at the same future timestamps.'],
[125,134,'A temporal weight combines their contributions along the complete horizon.'],
[134,142,'Configured scorers compare each complete candidate with the current reference.'],
[142,151,'Select an admitted update, or retain the current reference when replacement fails.'],
[151,160,'Endpoint feedback locates promising motions. Local search refines their shape and timing.'],
[160,168,'Search the trajectory at test time. Keep the driving models frozen.']];
const clamp=x=>Math.max(0,Math.min(1,x)),ease=x=>{x=clamp(x);return x*x*(3-2*x)},ramp=(t,a,b)=>ease((t-a)/(b-a)),f=x=>Number(x.toFixed(3));
const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;');
const text=(x,y,s,size=24,color=P.ink,weight=400,extra='')=>`<text x="${x}" y="${y}" fill="${color}" font-size="${size}" font-weight="${weight}" ${extra}>${esc(s)}</text>`;
const line=(x,y,u,v,color=P.line,w=2,extra='')=>`<path d="M${x},${y} L${u},${v}" stroke="${color}" stroke-width="${w}" fill="none" ${extra}/>`;
const dot=(x,y,r,color,extra='')=>`<circle cx="${f(x)}" cy="${f(y)}" r="${r}" fill="${color}" ${extra}/>`;
const pill=(x,y,w,s,color)=>`<rect x="${x}" y="${y}" width="${w}" height="29" rx="14.5" fill="${color}" opacity=".10"/>${text(x+w/2,y+20,s,14,color,600,'text-anchor="middle"')}`;
const arrow=(x,y,u,v,color=P.muted)=>line(x,y,u,v,color,1.8,`marker-end="url(#arrow)"`);
const base=x=>.7*Math.sin(x/15);
const roadHeading=x=>-16-Math.atan(.7/15*Math.cos(x/15))*180/Math.PI;
const trafficPose=t=>{const u=ramp(t,146,165),x=34+26*u;return {x,y:base(x)-.35,heading:roadHeading(x),phase:u};};
function shape(kind='reference',end=46,offset=0){
 return Array.from({length:121},(_,i)=>{const s=i/120,x=end*s;
  let y=base(x);const bump=Math.exp(-(((x-22)/6)**2));
  if(kind==='reference')y+=.32*bump+.25*s*s;
  if(kind==='endpoint')y+=.18*bump+offset*s*s;
  if(kind==='second')y-=.82*Math.exp(-(((x-26)/9)**2))+.48*s*s;
  if(kind==='center')y-=.23*bump+.10*s*s;
  if(kind==='proposal')y-=.42*bump+.10*s*s;
  if(kind==='control')y-=.25*Math.exp(-(((x-25)/8)**2))+.34*s*s;
  return [x,y];});
}
const blend=(a,b,p)=>a.map((q,i)=>[q[0]*(1-p)+b[i][0]*p,q[1]*(1-p)+b[i][1]*p]);
const ref=shape(),endpoint=shape('endpoint'),second=shape('second'),center=shape('center'),proposal=shape('proposal'),control=shape('control');
const final=proposal.map((p,i)=>{const w=ease(i/120);return [p[0]*(1-w)+control[i][0]*w,p[1]*(1-w)+control[i][1]*w]});
const proj=(x,y)=>[f(116+18*(x*.961262+y*.275637)),f(593+18*(-x*.275637+y*-.961262))];
const pts=a=>a.map(p=>proj(...p).join(',')).join(' ');
const path=(a,color,w=3,opacity=1,portion=1,dash='')=>`<polyline points="${pts(a.slice(0,Math.max(2,Math.round(a.length*clamp(portion)))))}" fill="none" stroke="${color}" stroke-width="${w}" stroke-linecap="round" stroke-linejoin="round" opacity="${opacity}" ${dash?`stroke-dasharray="${dash}"`:''}/>`;
const poseDots=(a,color)=>Array.from({length:8},(_,j)=>{const p=proj(...a[Math.round((j+1)*120/8)]);return dot(...p,3.2,'#fff',`stroke="${color}" stroke-width="2"`)}).join('');
const heading=(a,i)=>{const u=a[Math.max(0,i-1)],v=a[Math.min(120,i+1)];return -16-Math.atan2(v[1]-u[1],v[0]-u[0])*180/Math.PI};
function carGlyph(color='blue'){
 return `<g><ellipse cx="-2" cy="6" rx="43" ry="18" fill="#1B3340" opacity=".12"/>
 <g fill="#233B46"><rect x="-25" y="-18" width="15" height="6" rx="2"/><rect x="16" y="-18" width="15" height="6" rx="2"/><rect x="-25" y="12" width="15" height="6" rx="2"/><rect x="16" y="12" width="15" height="6" rx="2"/></g>
 <path d="M-41,-9 Q-41,-15 -33,-16 L24,-16 Q40,-14 42,-6 L42,6 Q40,14 24,16 L-33,16 Q-41,15 -41,9Z" fill="url(#car-${color})" stroke="#fff" stroke-width="1.3"/>
 <path d="M-22,-12 L9,-12 L21,-8 L23,0 L21,8 L9,12 L-22,12 L-29,8 L-30,0 L-29,-8Z" fill="#274453"/>
 <path d="M-17,-10 L7,-10 L10,10 L-17,10Z" fill="url(#car-${color})"/>
 <path d="M11,-10 L19,-7 Q23,0 19,7 L11,10Z" fill="url(#glass)"/>
 <path d="M-21,-10 L-27,-6 L-28,0 L-27,6 L-21,10Z" fill="#99B9C6"/>
 <path d="M25,-10 Q33,-9 36,-5 M25,10 Q33,9 36,5" fill="none" stroke="#fff1c6" stroke-width="3" stroke-linecap="round"/>
 <path d="M-36,-10 L-38,-5 M-36,10 L-38,5" stroke="#F17973" stroke-width="3" stroke-linecap="round"/>
 <path d="M8,-14 L13,-19 L17,-18 L15,-13 M8,14 L13,19 L17,18 L15,13" fill="#D5E4E9" stroke="#8099A6" stroke-width=".6"/>
 <path d="M26,-5 L35,-3 M26,5 L35,3 M-8,-8 L5,-8" stroke="#fff" stroke-opacity=".35" stroke-width="1"/>
 </g>`;
}
const car=(x,y,color='blue',a=-16,s=1,alpha=1)=>{const p=proj(x,y);return `<g transform="translate(${p}) rotate(${f(a)}) scale(${s})" opacity="${alpha}">${carGlyph(color)}</g>`};
const carOn=(a,i,color,s=1,alpha=1)=>car(...a[i],color,heading(a,i),s,alpha);
function person(x,y,scale=1){return `<g transform="translate(${x} ${y}) scale(${scale})"><ellipse cy="10" rx="13" ry="6" fill="#1E414C" opacity=".12"/><path d="M-4,4 L-8,12 M3,4 L8,10" stroke="#3B5264" stroke-width="5" stroke-linecap="round"/><path d="M-6,-2 L-13,4 M6,-2 L12,-6" stroke="#DCAC88" stroke-width="4" stroke-linecap="round"/><ellipse rx="8" ry="9" fill="#DF865E"/><circle cy="-8" r="5.5" fill="#E5B892"/><path d="M-5,-9 Q0,-17 5,-9" fill="#694B3E"/></g>`}
function cone(x,y,s=1){return `<g transform="translate(${x} ${y}) scale(${s})"><path d="M-10,7 L0,11 L10,7 L0,3Z" fill="#586872"/><path d="M-7,6 L0,-12 L7,6Z" fill="#E3A263" stroke="#BD8250"/><path d="M-3,-4 L3,-4 L5,0 L-5,0Z" fill="#fff8ec"/></g>`}
function tree(x,y,r=22){return `<g><ellipse cx="${x+3}" cy="${y+6}" rx="${r}" ry="${r*.74}" fill="#658A74" opacity=".12"/><circle cx="${x}" cy="${y}" r="${r}" fill="#B5CDBB"/><circle cx="${x-5}" cy="${y-5}" r="${r*.66}" fill="#C7DDCB"/><circle cx="${x+7}" cy="${y+4}" r="${r*.52}" fill="#A6C5B0"/></g>`}
function building(x,y,w,h){return `<g><path d="M${x+5},${y+7} h${w} v${h} h-${w}Z" fill="#C4D1D1" opacity=".5"/><rect x="${x}" y="${y}" width="${w}" height="${h}" rx="5" fill="#E5EAE7" stroke="#CFD8D5"/><rect x="${x+8}" y="${y+8}" width="${w-16}" height="${h-16}" rx="2" fill="#EEF2EE" stroke="#D8E0DC"/><path d="M${x+w*.3},${y+8} v${h-16} M${x+w*.65},${y+8} v${h-16}" stroke="#D6DFD9"/></g>`}
const roadPoints=Array.from({length:130},(_,i)=>[-8+i*.5,0]);
function road(){const xx=roadPoints.map(p=>p[0]);const boundary=o=>xx.map(x=>[x,base(x)+o]);
 return `<g clip-path="url(#map-clip)"><rect x="40" y="188" width="1004" height="523" rx="24" fill="#EDF3EE"/>
 ${building(140,259,118,68)}${building(314,226,130,62)}${building(500,209,145,60)}${building(756,198,121,57)}
 ${tree(112,214,24)}${tree(694,230,20)}${tree(950,247,26)}${tree(160,687,28)}${tree(431,660,24)}${tree(720,621,22)}${tree(991,598,25)}
 ${path(boundary(0),'#D1DCD7',160)}${path(boundary(0),'#C2CFD1',126)}${path(boundary(0),'#DDE5E7',120)}
 ${path(boundary(-3.1),'#FFFFFF',2)}${path(boundary(3.1),'#FFFFFF',2)}
 ${person(619,298,.9)}${person(650,289,.78)}${cone(761,555,.7)}${cone(783,548,.7)}${cone(805,542,.7)}
 ${car(22,base(22)+1.85,'silver',roadHeading(22),1.05)}
 ${text(400,395,'Parked vehicle',15,P.muted)}
 <path d="M72,656 L72,677 L93,677" stroke="#819B94" stroke-width="1.5" fill="none"/>${text(102,682,'Road-plane view',14,P.muted)}
 </g>`;
}
const defs=`<defs><clipPath id="map-clip"><rect x="40" y="188" width="1004" height="523" rx="24"/></clipPath>
 <linearGradient id="car-blue" x2="0" y2="1"><stop stop-color="#8BC5EF"/><stop offset=".45" stop-color="#4C98D7"/><stop offset="1" stop-color="#2776B9"/></linearGradient>
 <linearGradient id="car-gold" x2="0" y2="1"><stop stop-color="#F3D6A4"/><stop offset=".5" stop-color="#E0B36E"/><stop offset="1" stop-color="#BF8741"/></linearGradient>
 <linearGradient id="car-green" x2="0" y2="1"><stop stop-color="#A5DEC9"/><stop offset=".5" stop-color="#54B99C"/><stop offset="1" stop-color="#238E76"/></linearGradient>
 <linearGradient id="car-silver" x2="0" y2="1"><stop stop-color="#F6F8F7"/><stop offset=".5" stop-color="#C1CFD4"/><stop offset="1" stop-color="#8FA5AF"/></linearGradient>
 <linearGradient id="glass" x2="0" y2="1"><stop stop-color="#D4E7EF"/><stop offset="1" stop-color="#759CAF"/></linearGradient>
 <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="none" stroke="#81949A" stroke-width="1.2"/></marker>
 <linearGradient id="utility"><stop stop-color="#A8BDCF"/><stop offset=".5" stop-color="#A6CABB"/><stop offset="1" stop-color="#159B80"/></linearGradient></defs>`;
let seed=51294;const rand=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296};
const samples=Array.from({length:48},(_,i)=>{const spread=i<20?1:i<36?.57:.25;const x=46+(rand()-.5)*12*spread,y=-.22+(rand()-.5)*4*spread;return {x,y,u:Math.exp(-(((x-46)/4)**2)-((y+.22)/1.2)**2)}});
const uc=u=>{const a=[166,185,201],b=[21,155,128];return `rgb(${a.map((x,j)=>Math.round(x+(b[j]-x)*u)).join(',')})`};
function sideTitle(n,title,sub){return text(1100,218,n,14,P.green,700,'letter-spacing="2"')+text(1100,258,title,27,P.ink,600)+text(1100,289,sub,16,P.muted)}
function closeup(t,kind){
 if(kind==='timing'){
  const shift=ramp(t,12,17),egoX=1195+35*shift,leadX=1440;
  let s=sideTitle('DETAIL','Keep the vehicle ahead in view','Same lane. Same future timestamp.');
  s+=`<rect x="1095" y="326" width="445" height="255" rx="20" fill="#E7EDEF"/>`;
  s+=line(1110,375,1525,375,'#fff',3)+line(1110,524,1525,524,'#fff',3);
  s+=`<g transform="translate(${leadX} 448) scale(1.7)">${carGlyph('silver')}</g>`;
  s+=`<g transform="translate(${egoX} 448) scale(1.7)">${carGlyph(shift>.5?'gold':'green')}</g>`;
  const rear=leadX-41*1.7,front=egoX+42*1.7;
  s+=line(front,503,rear,503,P.green,2)+line(front,496,front,510,P.green,2)+line(rear,496,rear,510,P.green,2);
  s+=text((front+rear)/2,551,'Following gap',15,P.green,600,'text-anchor="middle"');
  s+=text(egoX,350,'Ego plan',16,P.ink,500,'text-anchor="middle"')+text(leadX,350,'Lead vehicle',16,P.ink,500,'text-anchor="middle"');
  s+=text(1100,622,'A forward shift reduces the gap',21,P.ink,500)+text(1100,657,'Longitudinal footprint comparison',15,P.muted);
  return s;
 }
 const shift=kind==='final'?1-ramp(t,144,150):ramp(t,5,11);
 let s=sideTitle('DETAIL','The vehicle occupies space','Small lateral shifts change clearance');
 s+=`<rect x="1095" y="326" width="445" height="255" rx="20" fill="#E7EDEF"/>`;
 s+=`<g transform="translate(1311 401) scale(2.05)">${carGlyph('silver')}</g>`;
 s+=`<g transform="translate(1311 ${505-12.5*shift}) scale(2.05)">${carGlyph(shift>.7?'gold':'green')}</g>`;
 s+=line(1120,563,1515,563,'#fff',3);
 s+=line(1510,438,1510,465-12.5*shift,P.green,2)+line(1502,438,1518,438,P.green,2)+line(1502,465-12.5*shift,1518,465-12.5*shift,P.green,2)+text(1100,622,'Small shifts change clearance',22,P.ink,500);
 return s+text(1100,657,'Enlarged footprint illustration',15,P.muted);
}
function archive(t){
 const n=Math.min(48,Math.max(0,Math.floor((t-21)/.64)));
 const hp=s=>[1114+(s.x-39)/14*398,332+(2.1-s.y)/4.3*232];
 let s=sideTitle('01 / FEEDBACK','Where can this path end?','Full-path utility at reached terminal states');
 s+=`<rect x="1096" y="317" width="446" height="270" rx="17" fill="#F0F5F3"/>`;
 for(let i=1;i<5;i++){s+=line(1109,327+i*48,1526,327+i*48,'#DEE8E3',1);s+=line(1110+i*82,330,1110+i*82,572,'#DEE8E3',1)}
 for(let i=0;i<n;i++){let q=samples[i],p=hp(q);s+=dot(...p,5.5,uc(q.u));}
 if(n>24){const p=hp({x:46,y:-.22}),rx=72-38*ramp(t,36,53);s+=`<ellipse cx="${p[0]}" cy="${p[1]}" rx="${rx}" ry="${rx*.85}" fill="#159B80" fill-opacity=".05" stroke="#159B80" stroke-width="1.8" stroke-dasharray="5 5"/>`;s+=text(1140,351,'Promising region',16,P.green,600)}
 s+=text(1110,613,'Lower utility',14,P.muted)+text(1415,613,'Higher utility',14,P.green);
 s+=`<rect x="1110" y="626" width="408" height="6" rx="3" fill="url(#utility)"/>`;
 s+=text(1100,673,'XY projection',17,P.ink,500)+pill(1244,653,52,'x',P.blue)+pill(1304,653,52,'y',P.blue)+pill(1364,653,75,'heading',P.muted)+pill(1447,653,70,'speed',P.muted);
 return {svg:s,n};
}
function miniature(a,x,y,w,h,color){const pp=a.map((p,i)=>`${f(x+w*i/120)},${f(y-h*(p[1]-base(p[0])))}`).join(' ');return `<polyline points="${pp}" fill="none" stroke="${color}" stroke-width="3" stroke-linecap="round"/>`}
function planners(t){
 let s=sideTitle('02 / REFINEMENT','Two planners. One center.','Keep both models frozen');
 for(let j=0;j<2;j++){
  const x=1100+j*234,col=j?P.gold:P.blue,a=j?second:endpoint;
  s+=pill(x,327,187,'Planner '+(j+1),col);
  for(let k=0;k<4;k++)s+=miniature(blend(a,center,k*.22),x+6,410,175,35,col);
  s+=arrow(x+93,449,1314+(j?22:-22),492,col);
 }
 s+=`<rect x="1110" y="508" width="408" height="111" rx="18" fill="#E9F3EF"/>`;
 s+=miniature(center,1132,574,361,44,P.green)+text(1130,541,'Shared center',18,P.green,600);
 if(t<77)s+=text(1100,658,'Bounded blend  →  geometric search',17,P.ink,500);
 else s+=pill(1100,646,135,'longitudinal',P.muted)+pill(1245,646,103,'lateral',P.muted)+pill(1358,646,130,'time scale',P.muted);
 return s;
}
function branches(t){
 let s=sideTitle('03 / LOCAL SEARCH','Two complementary branches','Both begin at the shared center');
 s+=miniature(center,1132,346,365,38,P.green)+text(1100,325,'Shared center',16,P.green,600);
 s+=arrow(1308,376,1190,405)+arrow(1314,376,1430,405);
 s+=text(1100,442,'Proposal',22,P.blue,600)+text(1350,442,'Control',22,P.purple,600);
 for(let k=0;k<4;k++)s+=miniature(blend(center,second,k*.16),1100,502,177,38,P.blue);
 s+=miniature(center,1350,502,170,38,'#B9C5C9')+miniature(control,1350,502,170,38,P.purple);
 s+=text(1100,555,'Cross-model drafts',15,P.muted)+text(1350,555,'Rollout difference',15,P.muted);
 s+=line(1100,584,1518,584,P.line,1);
 s+=text(1100,623,t<98?'Blend proposals around the center':'Center + bounded control residual',20,P.ink,500);
 s+=text(1100,656,t<98?'Evaluate each complete alternative':'Zero residual preserves the center',16,P.muted);
 return s;
}
function fusion(t){
 let s=sideTitle('04 / FUSE & COMPARE','Align the future timestamps','Compare the complete candidate with its reference');
 if(t<134){
  s+=miniature(proposal,1115,378,383,50,P.blue)+miniature(control,1115,449,383,50,P.purple);
  for(let i=0;i<8;i++){const x=1115+383*i/7; s+=line(x,401,x,445,'#D4DFE1',1,'stroke-dasharray="3 4"');s+=dot(x,378-50*(proposal[Math.round(i*120/7)][1]-base(proposal[Math.round(i*120/7)][0])),3,P.blue);s+=dot(x,449-50*(control[Math.round(i*120/7)][1]-base(control[Math.round(i*120/7)][0])),3,P.purple);}
  s+=text(1100,335,'Proposal branch',16,P.blue,600)+text(1100,491,'Control branch',16,P.purple,600);
  s+=`<path d="M1120,584 C1250,584 1360,520 1500,520" fill="none" stroke="${P.green}" stroke-width="3"/>`;
  let z=clamp((t-116)/18),x=1120+380*z,y=584-64*ease(z);s+=dot(x,y,7,P.green,'stroke="#fff" stroke-width="2"');
  s+=text(1100,625,'Weight changes along the horizon',18,P.ink,500)+text(1100,663,'8 corresponding future poses',16,P.muted);
 }else{
  for(let j=0;j<2;j++){
   const y=340+j*103,col=j?P.gold:P.blue;s+=text(1100,y,'Scorer '+(j+1),17,col,600);
   s+=`<rect x="1100" y="${y+15}" width="420" height="59" rx="12" fill="${col}" opacity=".07"/>`;
   s+=text(1115,y+51,'Reference',16,P.muted)+text(1247,y+51,'Candidate',16,col,600)+text(1405,y+51,'+ gain',16,P.green,600);
  }
  s+=text(1100,589,'Matched context within each comparison',16,P.muted);
  s+=text(1100,636,'Admit  →  rank  →  keep or replace',20,P.ink,600);
  s+=text(1100,669,'Stage-specific checks; current reference retained',14,P.muted);
 }
 return s;
}
function render(t){
 t=Math.max(0,Math.min(D-.001,t));const idx=phases.findIndex(a=>t>=a[0]&&t<a[1]);
 const titles=['A line is only the beginning.','Search the endpoint region.','Make the full path precise.','Refine the same starting plan.','Combine motion. Compare gains.','Return one complete trajectory.'];
 let out=`<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900"><style>text{font-family:Arial,Helvetica,sans-serif}path,polyline{stroke-linejoin:round}</style>${defs}<rect width="1600" height="900" fill="${P.paper}"/>`;
 out+=text(48,52,'DriveTTO',29,P.ink,700)+text(1550,48,'TEST-TIME TRAJECTORY OPTIMIZATION',13,P.muted,600,'letter-spacing="2" text-anchor="end"');
 out+=text(47,118,titles[idx],43,P.ink,600);
 out+=text(49,156,phases[idx][2],13,P.green,700,'letter-spacing="2.3"');
 out+=line(1070,198,1070,710,P.line,1);
 out+=road();
 let map='',right='',legend='';
 const run=ramp(t,146,165),lead=trafficPose(t);
 map+=car(lead.x,lead.y,'silver',lead.heading,.9);
 if(t<146){const a=proj(lead.x+2.9,lead.y),b=proj(lead.x+5.2,base(lead.x+5.2)-.35);map+=arrow(...a,...b,P.muted)+text(a[0]-50,a[1]-40,'Lead vehicle',15,P.muted);}
 if(t<18){
  map+=path(ref,P.gold,4)+poseDots(ref,P.gold);
  if(t>5)map+=path(ref.map(p=>[p[0],p[1]-.35*ramp(t,5,11)]),P.green,3,.7);
  map+=carOn(ref,57,'gold');right=closeup(t,t<12?'lateral':'timing');legend='A complete plan includes the vehicle footprint';
 }else if(t<58){
  const a=archive(t);right=a.svg;const n=a.n;map+=path(ref,'#9AAEB7',2,.8,1,'6 7');
  for(let i=0;i<n;i++){const q=samples[i],a=shape('endpoint',q.x,q.y),p=proj(...a[120]);map+=path(a,uc(q.u),1.5,.22)+dot(...p,3.5,uc(q.u));}
  if(t>=21&&n<48){const q=samples[n],a=shape('endpoint',q.x,q.y),frac=ramp((t-21)%.64,0,.51),p=proj(...a[Math.round(120*frac)]);map+=path(a,P.green,3.5,.95,frac)+dot(...p,5,P.green);const e=proj(...a[120]);map+=`<circle cx="${e[0]}" cy="${e[1]}" r="11" fill="none" stroke="${P.gold}" stroke-width="1.5" stroke-dasharray="3 3"/>`;}
  if(t>51)map+=path(endpoint,P.green,4.5,1,ramp(t,51,55))+poseDots(endpoint,P.green);
  legend=t<33?'Request → complete path → score → reached state':'The next requests use feedback from completed paths';
 }else if(t<88){
  right=planners(t);const cur=t<77?blend(endpoint,second,.4*ramp(t,66,76)):blend(blend(endpoint,second,.4),center,ramp(t,77,85));
  map+=path(endpoint,P.blue,3,.7)+path(second,P.gold,3,.7,ramp(t,59,65))+path(cur,P.green,4)+poseDots(cur,P.green)+carOn(cur,57,'green');
  legend='Endpoint plan + Planner 2 proposal → shared center';
 }else if(t<116){
  right=branches(t);map+=path(center,'#97AAB2',2,1,1,'6 6');
  for(let k=0;k<5;k++)map+=path(blend(center,second,k*.12),P.blue,1.6,.20);
  map+=path(proposal,P.blue,3.5,1,ramp(t,89,97))+path(control,P.purple,3.5,1,ramp(t,98,107))+carOn(center,57,'green');
  legend='Proposal and control branches share the same center';
 }else if(t<142){
  right=fusion(t);const cur=blend(proposal,final,ramp(t,116,131));map+=path(proposal,P.blue,2.4,.65)+path(control,P.purple,2.4,.65)+path(cur,P.green,4.5)+poseDots(cur,P.green);
  const i=Math.round(ramp(t,117,132)*120),a=proj(...proposal[i]),b=proj(...control[i]);map+=line(...a,...b,P.muted,1.5)+dot(...proj(...cur[i]),6,P.green,'stroke="#fff" stroke-width="2"');
  legend='Blend corresponding future poses, then evaluate the whole path';
 }else{
  right=closeup(t,'final');map+=path(ref,P.gold,2,.55,1,'7 7')+path(final,P.green,4)+poseDots(final,P.green);
  for(let i of [25,45,65,85,105])map+=carOn(final,i,'green',1,.12);
  map+=carOn(final,Math.round(run*120),'green');legend='The selected complete plan becomes the new reference';
 }
 if(t<146)map+=car(0,0,'blue');
 out+=`<g clip-path="url(#map-clip)">${map}</g>${right}`;
 out+=dot(60,746,4,P.green)+text(75,752,legend,18,P.ink,500);
 const cap=caps.find(a=>t>=a[0]&&t<a[1])[2];out+=line(48,780,1552,780,P.line,1)+text(48,821,cap,22,P.ink);
 out+=text(48,867,'NAV1 Full · Illustrative geometry and utility · Frozen planners',13,P.muted);
 phases.forEach((a,j)=>{const x=1138+j*70;out+=`<rect x="${x}" y="860" width="56" height="3" rx="1.5" fill="${P.line}"/><rect x="${x}" y="860" width="${56*clamp((t-a[0])/(a[1]-a[0]))}" height="3" rx="1.5" fill="${P.green}"/>`});
 return out+'</svg>';
}
const api={render,phases,caps,duration:D,width:W,height:H,trafficPose,roadHeading,base};
if(typeof module!=='undefined')module.exports=api;else root.DriveTTOMotion=api;
})(typeof window==='undefined'?{}:window);
