from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=(R/'docs/assets/animation/method-svg.js').read_text(encoding='utf-8')
s=s.replace('Position and arrival time also determine how the plan meets crossing traffic.','Longitudinal changes alter the gap to the vehicle ahead at the same timestamp.')
s=s.replace('const base=x=>.7*Math.sin(x/15);','const base=x=>.7*Math.sin(x/15);\nconst roadHeading=x=>-16-Math.atan(.7/15*Math.cos(x/15))*180/Math.PI;\nconst trafficPose=t=>{const u=ramp(t,146,165),x=34+26*u;return {x,y:base(x)-.35,heading:roadHeading(x),phase:u};};')
s=s.replace("${path(boundary(-3.1),'#FFFFFF',2)}${path(boundary(3.1),'#FFFFFF',2)}${path(boundary(.1),'#FFFFFF',2,.9,1,'13 16')}","${path(boundary(-3.1),'#FFFFFF',2)}${path(boundary(3.1),'#FFFFFF',2)}")
s=s.replace("${car(22,base(22)+1.85,'silver',-18,1.05)}","${car(22,base(22)+1.85,'silver',roadHeading(22),1.05)}")
a=s.index('function closeup(t,kind){');b=s.index('\nfunction archive(t)',a)
s=s[:a]+'''function closeup(t,kind){
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
}''' + s[b:]
old=" const run=ramp(t,146,165),cy=t>146?base(35)+6-12*ramp(run,.18,.60):base(35)+4.4;\n map+=car(35,cy,'silver',74,.9);"
assert old in s
s=s.replace(old," const run=ramp(t,146,165),lead=trafficPose(t);\n map+=car(lead.x,lead.y,'silver',lead.heading,.9);\n if(t<146){const a=proj(lead.x+2.9,lead.y),b=proj(lead.x+5.2,base(lead.x+5.2)-.35);map+=arrow(...a,...b,P.muted)+text(a[0]-50,a[1]-40,'Lead vehicle',15,P.muted);}")
s=s.replace('const api={render,phases,caps,duration:D,width:W,height:H};','const api={render,phases,caps,duration:D,width:W,height:H,trafficPose,roadHeading,base};')
assert "'silver',74" not in s and 'rotate(90)' not in s and 'crossing traffic' not in s
(R/'docs/assets/animation/method-svg-traffic-20261031.js').write_text(s,encoding='utf-8')
rend=(R/'tools/render_svg_method.cjs').read_text(encoding='utf-8').replace('method-svg.js','method-svg-traffic-20261031.js').replace('audit/svg_method_20261031_v1','audit/svg_traffic_20261031_v1').replace('.method-svg-20261031-v1','.method-svg-traffic-20261031-v1')
(R/'tools/render_svg_traffic.cjs').write_text(rend,encoding='utf-8')
html=(R/'docs/method-animation.html').read_text(encoding='utf-8').replace('assets/animation/method-svg.js','assets/animation/method-svg-traffic-20261031.js')
(R/'docs/method-animation.html').write_text(html,encoding='utf-8')
print('TRAFFIC_SOURCE_PREPARED')
