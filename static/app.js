const file = document.getElementById('file');
const target = document.getElementById('target');
const button = document.getElementById('submit');
const label = document.getElementById('file-label');
const status = document.getElementById('status');
const drop = document.getElementById('drop');
const formats = {
  jpg:['png','webp','pdf'], jpeg:['png','webp','pdf'],
  png:['jpg','webp','pdf'], webp:['jpg','png','pdf'], bmp:['jpg','png','webp','pdf'],
  docx:['pdf'], pdf:['docx','pngzip']
};
const labels = {jpg:'JPG image',png:'PNG image',webp:'WebP image',pdf:'PDF document',docx:'Word document (.docx)',pngzip:'PNG pages (.zip)'};
function setStatus(message,type=''){status.textContent=message;status.className=type;}
function syncFile(){
  const chosen=file.files[0];
  label.textContent=chosen?chosen.name:'Choose a file or drop it here';
  const extension=chosen?.name.split('.').pop().toLowerCase();
  const options=formats[extension]||[];
  target.replaceChildren();
  if(options.length){for(const option of options){const node=document.createElement('option');node.value=option;node.textContent=labels[option];target.append(node);}}
  else {const node=document.createElement('option');node.textContent='Unsupported format';node.value='';target.append(node);}
  target.disabled=!options.length;button.disabled=!options.length;
  const tooLarge=chosen?.size>15*1024*1024;
  if(tooLarge){button.disabled=true;setStatus('The file exceeds the 15 MB limit.','error');}else setStatus('');
}
file.addEventListener('change',syncFile);
for(const eventName of ['dragenter','dragover'])drop.addEventListener(eventName,e=>{e.preventDefault();drop.classList.add('drag');});
for(const eventName of ['dragleave','drop'])drop.addEventListener(eventName,e=>{e.preventDefault();drop.classList.remove('drag');});
drop.addEventListener('drop',e=>{if(e.dataTransfer.files.length){file.files=e.dataTransfer.files;syncFile();}});
document.getElementById('converter').addEventListener('submit',async event=>{
  event.preventDefault();if(!file.files[0]||!target.value)return;
  button.disabled=true;setStatus('Converting…');
  const form=new FormData();form.append('file',file.files[0]);form.append('to',target.value);
  try{
    const response=await fetch('/api/convert',{method:'POST',body:form});
    if(!response.ok){const payload=await response.json().catch(()=>({detail:'Conversion failed'}));throw new Error(typeof payload.detail==='string'?payload.detail:'Conversion failed');}
    const blob=await response.blob();
    const url=URL.createObjectURL(blob);
    const header=response.headers.get('content-disposition')||'';
    const name=/filename="([^"]+)"/.exec(header)?.[1]||'converted-file';
    const link=document.createElement('a');link.href=url;link.download=name;document.body.append(link);link.click();link.remove();
    setTimeout(()=>URL.revokeObjectURL(url),10000);
    setStatus('Conversion complete. Download started.','success');
  }catch(error){setStatus(error.message,'error');}finally{button.disabled=false;}
});