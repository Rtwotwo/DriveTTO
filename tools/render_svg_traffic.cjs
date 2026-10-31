// SVG is the only drawing source. Sharp/librsvg rasterizes it; ffmpeg encodes.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{spawn}=require('child_process'),{once}=require('events');
const root=path.resolve(__dirname,'..'),A=require(path.join(root,'docs/assets/animation/method-svg-traffic-20261031.js'));
const sharp=require(process.env.DRIVETTO_NODE_MODULES?path.join(process.env.DRIVETTO_NODE_MODULES,'sharp'):'sharp');
const args=process.argv.slice(2),value=(k,f)=>args.includes(k)?args[args.indexOf(k)+1]:f;
const out=path.resolve(value('--out',path.join(root,'audit/svg_traffic_20261031_v1')));fs.mkdirSync(out,{recursive:true});
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
async function main(){
 if(args.includes('--preview')){
  const times=[5,14,28,40,54,64,74,84,94,105,120,138,145,157,165];
  for(const t of times){const svg=A.render(t);fs.writeFileSync(path.join(out,`frame-${String(t).padStart(3,'0')}.svg`),svg);await sharp(Buffer.from(svg)).png().toFile(path.join(out,`frame-${String(t).padStart(3,'0')}.png`));}
  const thumbs=await Promise.all(times.map(async(t,i)=>({input:await sharp(path.join(out,`frame-${String(t).padStart(3,'0')}.png`)).resize(528,297).png().toBuffer(),left:i%3*536,top:Math.floor(i/3)*307})));
  await sharp({create:{width:1600,height:1535,channels:3,background:'#edf2ef'}}).composite(thumbs).jpeg({quality:92}).toFile(path.join(out,'contact.jpg'));
  console.log('SVG_PREVIEW_OK',times.length);return;
 }
 const start=Number(value('--start',0)),end=Number(value('--end',168)),fps=24;
 const remote='/data/xinyao/release/DriveTTO/.method-svg-traffic-20261031-v1',name=`method-${String(start).padStart(3,'0')}-${String(end).padStart(3,'0')}.mp4`;
 const cmd=`mkdir -p ${remote} && test ! -e ${remote}/${name} && ffmpeg -nostdin -hide_banner -loglevel error -f image2pipe -framerate 24 -vcodec png -i pipe:0 -an -c:v libx264 -preset medium -crf 19 -pix_fmt yuv420p -threads 3 -movflags +faststart ${remote}/${name}`;
 const proc=spawn('ssh',['-p','32000','-o','BatchMode=yes','-o','StrictHostKeyChecking=no','-o','UserKnownHostsFile=/dev/null','root@8.130.174.55',cmd],{stdio:['pipe','pipe','pipe'],windowsHide:true});
 let errors='';proc.stderr.on('data',b=>{errors+=b;process.stderr.write(b)});proc.stdout.on('data',b=>process.stdout.write(b));
 const done=once(proc,'close');const begin=Date.now();let count=0;
 for(let i=start*fps;i<end*fps;i++){
  const png=await sharp(Buffer.from(A.render(i/fps))).resize(1280,720).png({compressionLevel:2,adaptiveFiltering:false}).toBuffer();
  if(!proc.stdin.write(png))await once(proc.stdin,'drain');count++;
  if(count%240===0)console.log(JSON.stringify({start,end,frames:count,total:(end-start)*fps,elapsed_s:(Date.now()-begin)/1000}));
 }
 proc.stdin.end();const [code]=await done;fs.writeFileSync(path.join(out,name+'.exit.json'),JSON.stringify({code,start,end,frames:count,fps,elapsed_s:(Date.now()-begin)/1000,source_sha256:sha(fs.readFileSync(path.join(root,'docs/assets/animation/method-svg-traffic-20261031.js'))),stderr:errors},null,2));
 if(code!==0)throw Error('ffmpeg SSH exit '+code);console.log('SVG_RENDER_COMPLETE',name,count);
}
main().catch(e=>{console.error(e);process.exitCode=1});
