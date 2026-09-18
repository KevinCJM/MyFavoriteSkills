// Exercise the built output used by stdio clients, not a separate formatter mock.
import assert from 'node:assert/strict';
import { test } from 'vitest';
import {pathToFileURL, fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('..', import.meta.url));
const {withStructuredText}=await import(pathToFileURL(`${root}/dist/mcp-server.js`));
const text='完整结论：Secret 的保证是有条件的；引用 script.sh:20。'.repeat(100);
function fixture(status='completed') {
  return {content:[{type:'text',text}], ...(status==='failed'?{isError:true}:{}), structuredContent:{
    jobId:'job_1',sessionId:'ses_1',messageId:'msg_1',directory:'/tmp/review',status,
    inputs:[{id:'perm_1',type:'permission',permission:'edit'}], timedOut:false,
    result:{info:{role:'assistant',sessionID:'ses_1',parentID:'msg_1',tokens:{reasoning:17}},
      parts:[{type:'text',text},{type:'tool',state:{status:'error',error:'MUST_KEEP_ERROR',output:{text:'MUST_KEEP_DATA'}}}]},
    error:status==='failed'?{name:'ProviderError',message:'MUST_KEEP_FAILURE'}:undefined,
  }};
}
test('default contract is unchanged',()=>{const r=fixture();assert.deepEqual(withStructuredText(r),{...r,structuredContent:{...r.structuredContent,text,isError:false}})});
test('compact keeps one complete report plus correlation and metadata without input mutation',()=>{
  const r=fixture(), before=structuredClone(r), compact=withStructuredText(r,true), data=compact.structuredContent;
  assert.deepEqual(r,before);assert.equal(data.text,text);
  for(const k of ['jobId','sessionId','messageId','directory','status','inputs','timedOut']) assert.deepEqual(data[k],r.structuredContent[k]);
  assert.deepEqual(data.result.info,r.structuredContent.result.info);
  assert.deepEqual(data.result.parts,[r.structuredContent.result.parts[1]]);
  assert.equal(data.fullResultTool,'opencode_job_get');
  assert.equal(JSON.stringify(compact).split(text).length-1,1);
  assert.ok(JSON.stringify(compact).length < JSON.stringify(withStructuredText(r)).length*0.5);
});
for(const status of ['accepted','running','input_required','completed','failed','cancelled','unknown']) test(`state ${status} retains errors/inputs/flags`,()=>{
  const r=fixture(status);const out=withStructuredText(r,true);
  assert.equal(out.structuredContent.status,status);assert.deepEqual(out.structuredContent.inputs,r.structuredContent.inputs);
  assert.deepEqual(out.structuredContent.error,r.structuredContent.error);assert.equal(out.isError,r.isError);
  assert.equal(out.structuredContent.isError,status==='failed');
});
test('opaque business JSON that resembles a message is retained',()=>{
 const r=fixture();r.structuredContent.result={info:{role:'assistant'},parts:[{type:'text',text}]};
 assert.deepEqual(withStructuredText(r,true).structuredContent.result,r.structuredContent.result);
});
test('structured output and mismatched message identity stay intact',()=>{
 for(const change of [r=>r.structuredContent.result.info.structured={result:text},r=>r.structuredContent.result.info.parentID='another']) {
 const r=fixture();change(r);assert.deepEqual(withStructuredText(r,true).structuredContent.result,r.structuredContent.result);
 }
});
test('text not present in canonical answer is retained',()=>{
 const r=fixture();r.structuredContent.result.parts.push({type:'text',text:'UNMERGED_TEXT'});
 assert.ok(withStructuredText(r,true).structuredContent.result.parts.some(p=>p.text==='UNMERGED_TEXT'));
});
test('nontext attachments and nonjob results remain intact',()=>{
 const r=fixture();const media={type:'image',data:'YWJj',mimeType:'image/png'};r.content.push(media);
 assert.deepEqual(withStructuredText(r,true).content[1],media);
 const ordinary={content:[{type:'text',text:'ordinary'}]};assert.deepEqual(withStructuredText(ordinary,true),withStructuredText(ordinary));
});
