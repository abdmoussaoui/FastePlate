'use strict';
const $ = id => document.getElementById(id);
const state = {file:null, preview:null, job:null, selected:0, busy:false, saving:false, exporting:false, drafts:new Map(), generation:0};
const percent = value => value == null ? '—' : `${(value * 100).toFixed(1)}%`;

function notice(message='') {
  $('notice').textContent=message;
  $('notice').hidden=!message;
}
function status(message) { $('status').textContent=message; }
function controls() {
  const locked=state.busy || state.saving || state.exporting;
  $('choose-button').disabled=locked;
  $('file-input').disabled=locked;
  $('mode').disabled=locked;
  $('confidence').disabled=locked;
  $('analyze-button').disabled=locked || !state.file;
  $('analyze-label').textContent=state.busy?'Analyzing…':'Analyze image';
  $('export-button').disabled=locked || !state.job || state.drafts.size>0;
  $('export-button').title=state.drafts.size ? 'Save or reset your corrections before exporting.' : 'Download annotated image, crops, CSV, TXT and JSON';
  const plate=state.job?.plates[state.selected];
  $('correction').disabled=locked || !plate;
  $('save-correction').disabled=locked || !plate || !state.drafts.has(state.selected);
  $('reset-correction').disabled=locked || !plate || (plate.corrected_text==null && !state.drafts.has(state.selected));
  $('original-button').disabled=!state.file || state.busy;
  $('detection-button').disabled=!state.job || state.busy;
  $('processing-overlay').hidden=!state.busy;
}
function renderReading(element,text) {
  element.replaceChildren();
  const parts=(text || '—').split(/\s+/u);
  for (const part of parts) {
    const fragment=document.createElement('bdi');
    fragment.dir='auto';
    fragment.textContent=part;
    element.append(fragment);
  }
}
function resetInspection() {
  $('crop-image').hidden=true;
  $('crop-image').removeAttribute('src');
  $('crop-placeholder').hidden=false;
  $('crop-placeholder').textContent='The detected plate will appear here.';
  $('plate-number').textContent='—';
  $('reading-tag').textContent='Awaiting analysis';
  $('ocr-reading').textContent='—';
  $('detection-score').textContent='—';
  $('ocr-score').textContent='—';
  $('correction').value='';
  $('correction-status').textContent='Original OCR is always preserved.';
  $('review-note').textContent='Automatic readings can miss letters or confuse digits. Inspect the crop before exporting.';
}
function emptyTable(message) {
  $('results-body').replaceChildren();
  const row=document.createElement('tr'); row.className='empty-row';
  const cell=document.createElement('td'); cell.colSpan=6; cell.textContent=message;
  row.append(cell); $('results-body').append(row);
  $('plate-count').textContent='0';
}
function showView(detection) {
  if (detection && !state.job) return;
  $('main-image').src=detection?state.job.annotated_url:(state.job?.original_url || state.preview);
  $('main-image').alt=detection?'Image with detected license plate bounding boxes':'Original uploaded image';
  $('original-button').classList.toggle('active',!detection);
  $('detection-button').classList.toggle('active',detection);
  $('original-button').setAttribute('aria-pressed',String(!detection));
  $('detection-button').setAttribute('aria-pressed',String(detection));
}
function selectPlate(index) {
  const plate=state.job?.plates[index];
  if (!plate) return;
  state.selected=index;
  for (const row of $('results-body').children) row.classList.toggle('selected',Number(row.dataset.index)===index);
  $('crop-image').src=plate.crop_url;
  $('crop-image').hidden=false;
  $('crop-placeholder').hidden=true;
  $('plate-number').textContent=`${String(index+1).padStart(2,'0')} / ${String(state.job.plates.length).padStart(2,'0')}`;
  $('reading-tag').textContent=plate.raw_text?'Review required':'No text read';
  renderReading($('ocr-reading'),plate.raw_text);
  $('detection-score').textContent=percent(plate.detection_confidence);
  $('ocr-score').textContent=percent(plate.ocr_confidence);
  $('review-note').textContent=!plate.raw_text?'No text was recognized. Try another preprocessing option or enter a manual correction.':plate.ocr_confidence<.65?'Low OCR confidence. Check every digit and the Arabic letter against the crop.':'Automatic reading: inspect all fields. OCR confidence does not guarantee a correct registration.';
  $('correction').value=state.drafts.get(index) ?? plate.corrected_text ?? '';
  $('correction-status').textContent=state.drafts.has(index)?'Unsaved correction. Save before exporting.':plate.corrected_text!=null?'Correction saved. Original OCR preserved.':'Original OCR is always preserved.';
  controls();
}
function renderTable() {
  if (!state.job.plates.length) {
    emptyTable('No plates detected. Try a clearer image or lower the detection threshold.');
    return;
  }
  $('results-body').replaceChildren();
  $('plate-count').textContent=String(state.job.plates.length);
  state.job.plates.forEach((plate,index) => {
    const row=document.createElement('tr'); row.className='plate-row'; row.dataset.index=String(index);
    const number=document.createElement('td');
    const button=document.createElement('button'); button.className='row-select'; button.textContent=String(index+1).padStart(2,'0'); button.setAttribute('aria-label',`Inspect plate ${index+1}`);
    number.append(button); row.append(number);
    const detection=document.createElement('td'); detection.textContent=percent(plate.detection_confidence); row.append(detection);
    const raw=document.createElement('td'); const reading=document.createElement('span'); reading.className='table-reading'; reading.dir='ltr'; renderReading(reading,plate.raw_text); raw.append(reading); row.append(raw);
    const score=document.createElement('td'); score.textContent=percent(plate.ocr_confidence); row.append(score);
    const correction=document.createElement('td'); const corrected=document.createElement('span'); corrected.className='table-reading'; corrected.dir='ltr'; renderReading(corrected,plate.corrected_text); correction.append(corrected); row.append(correction);
    const review=document.createElement('td'); const badge=document.createElement('span'); badge.className=`review-badge${plate.corrected_text!=null?' corrected':''}`; badge.textContent=plate.corrected_text!=null?'Corrected':'Check reading'; review.append(badge); row.append(review);
    row.addEventListener('click',()=>selectPlate(index));
    $('results-body').append(row);
  });
}
async function chooseFile(file) {
  if (!file || state.busy || state.saving || state.exporting) return;
  notice();
  if (file.size>20*1024*1024) {notice('Image exceeds 20 MB. Please choose a smaller file.');return;}
  if (!/\.(jpe?g|png|bmp|webp)$/i.test(file.name)) {notice('Choose a JPG, PNG, BMP or WebP image.');return;}
  const generation=++state.generation;
  const url=URL.createObjectURL(file);
  const image=new Image();
  try {
    await new Promise((resolve,reject)=>{image.onload=resolve;image.onerror=reject;image.src=url;});
  } catch {
    URL.revokeObjectURL(url); if(generation===state.generation)notice('This image could not be displayed. Choose a different file.');return;
  }
  if(generation!==state.generation){URL.revokeObjectURL(url);return;}
  if(image.naturalWidth*image.naturalHeight>12_000_000){URL.revokeObjectURL(url);notice('Image exceeds 12 megapixels. Resize it before uploading.');return;}
  if(state.preview)URL.revokeObjectURL(state.preview);
  state.preview=url;state.file=file;state.job=null;state.selected=0;state.drafts.clear();
  $('filename').textContent=file.name; $('filename').title=file.name;
  $('choose-label').textContent='Replace image';
  $('image-meta').textContent=`${image.naturalWidth.toLocaleString()} × ${image.naturalHeight.toLocaleString()} px · ${(file.size/1024/1024).toFixed(2)} MB`;
  $('empty-state').hidden=true;$('main-image').hidden=false;$('drop-zone').classList.add('has-image');
  $('download-annotated').hidden=true;
  showView(false);resetInspection();emptyTable('Image ready. Start analysis to detect and read its plates.');
  status('Image ready for analysis');controls();
}
async function api(url,options={}) {
  const response=await fetch(url,{...options,headers:{'X-FastePlate':'1',...options.headers},credentials:'same-origin'});
  const data=await response.json().catch(()=>({error:'Unexpected response from the server.'}));
  if(!response.ok)throw new Error(data.error || `Request failed (${response.status})`);
  return data;
}
async function poll(jobId) {
  let failures=0;
  for(;;) {
    let job;
    try { job=await api(`/api/jobs/${jobId}`);failures=0; }
    catch(error){if(++failures>=4)throw error;await new Promise(resolve=>setTimeout(resolve,1500));continue;}
    $('progress-message').textContent=job.message;
    status(job.message);
    if(job.state==='error')throw new Error(job.error || 'Analysis failed.');
    if(job.state==='done')return job;
    await new Promise(resolve=>setTimeout(resolve,700));
  }
}
async function analyze() {
  if(!state.file || state.busy)return;
  const confidence=Number($('confidence').value);
  if(!$('confidence').value || !Number.isFinite(confidence) || confidence<.05 || confidence>.95){notice('Detection threshold must be between 0.05 and 0.95.');return;}
  notice();state.busy=true;state.job=null;state.drafts.clear();state.selected=0;
  showView(false);resetInspection();emptyTable('Analysis in progress…');$('download-annotated').hidden=true;
  $('progress-message').textContent='Preparing the models…';status('Starting analysis…');controls();
  const body=new FormData();body.append('image',state.file);body.append('mode',$('mode').value);body.append('confidence',String(confidence));
  try {
    const queued=await api('/api/jobs',{method:'POST',body});
    state.job=await poll(queued.id);
    renderTable();
    if(state.job.plates.length)selectPlate(0);
    else {$('crop-placeholder').textContent='No plates detected in this image.';$('reading-tag').textContent='No detection';}
    showView(true);
    $('download-annotated').href=`${state.job.annotated_url}?download=1`;
    $('download-annotated').hidden=false;
    status(`${state.job.plates.length} plate${state.job.plates.length===1?'':'s'} · ${state.job.seconds.toFixed(2)} s processing · ${state.job.initialization_seconds.toFixed(2)} s model initialization`);
  } catch(error) {
    notice(error.message || 'Could not connect to the server. Check that python app.py is running.');
    emptyTable('Analysis did not complete. Check the message above and try again.');status('Analysis failed');
  } finally {state.busy=false;controls();}
}
async function saveCorrection(reset=false) {
  const index=state.selected;
  if(!state.job || state.saving)return;
  state.saving=true;notice();controls();
  try {
    state.job=await api(`/api/jobs/${state.job.id}/plates/${index}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:reset?null:$('correction').value})});
    state.drafts.delete(index);renderTable();selectPlate(index);
  } catch(error){notice(error.message);}
  finally{state.saving=false;controls();}
}
async function downloadExport() {
  if(!state.job || state.drafts.size || state.exporting)return;
  state.exporting=true;notice();controls();
  try {
    const response=await fetch(`/api/jobs/${state.job.id}/export`,{credentials:'same-origin'});
    if(!response.ok){const data=await response.json();throw new Error(data.error || 'Export failed.');}
    const url=URL.createObjectURL(await response.blob());
    const link=document.createElement('a');link.href=url;link.download='FastePlate_results.zip';document.body.append(link);link.click();link.remove();
    setTimeout(()=>URL.revokeObjectURL(url),10000);status('Export downloaded · images, crops, CSV, TXT and JSON');
  } catch(error){notice(error.message || 'Export failed.');}
  finally{state.exporting=false;controls();}
}
$('choose-button').addEventListener('click',()=>$('file-input').click());
$('file-input').addEventListener('change',event=>{chooseFile(event.target.files[0]);event.target.value='';});
$('drop-zone').addEventListener('click',()=>{if(!state.file && !state.busy)$('file-input').click();});
$('drop-zone').addEventListener('keydown',event=>{if((event.key==='Enter'||event.key===' ')&&!state.busy){event.preventDefault();$('file-input').click();}});
for(const name of ['dragenter','dragover'])$('drop-zone').addEventListener(name,event=>{event.preventDefault();if(!state.busy)$('drop-zone').classList.add('drag-over');});
$('drop-zone').addEventListener('dragleave',()=>$('drop-zone').classList.remove('drag-over'));
$('drop-zone').addEventListener('drop',event=>{event.preventDefault();$('drop-zone').classList.remove('drag-over');chooseFile(event.dataTransfer.files[0]);});
window.addEventListener('dragover',event=>event.preventDefault());window.addEventListener('drop',event=>event.preventDefault());
$('analyze-button').addEventListener('click',analyze);
$('original-button').addEventListener('click',()=>showView(false));
$('detection-button').addEventListener('click',()=>showView(true));
$('correction').addEventListener('input',()=>{state.drafts.set(state.selected,$('correction').value);$('correction-status').textContent='Unsaved correction. Save before exporting.';controls();});
$('correction').addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.isComposing){event.preventDefault();saveCorrection();}});
$('save-correction').addEventListener('click',()=>saveCorrection());
$('reset-correction').addEventListener('click',()=>saveCorrection(true));
$('export-button').addEventListener('click',downloadExport);
window.addEventListener('beforeunload',event=>{if(state.drafts.size){event.preventDefault();event.returnValue='';}});
controls();
