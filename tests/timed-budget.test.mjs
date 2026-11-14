import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
const source=readFileSync(new URL('../scripts/ig-soft-timed.mjs',import.meta.url),'utf8');
const waitCode=source.slice(source.indexOf('  const wait = async'),source.indexOf('  const note ='));
function budget(clock,deadline){
  const sandbox={inputs:{},deadline,Date:{now:()=>clock.now},SessionBudgetComplete:class extends Error{},
    page:{waitForTimeout:async ms=>{clock.now+=ms;}}};
  return vm.runInNewContext(waitCode+'\nwait',sandbox);
}
test('wait is clipped at the duration deadline and ends the session',async()=>{
  const clock={now:0};await assert.rejects(budget(clock,100)(1000));assert.equal(clock.now,100);
});
test('wait after expiry does not execute another browser wait',async()=>{
  const clock={now:101};await assert.rejects(budget(clock,100)(10));assert.equal(clock.now,101);
});
test('ordinary waits finish before the budget',async()=>{
  const clock={now:0};await budget(clock,100)(10);assert.equal(clock.now,10);
});

test('hard timer closes only its dedicated session tab',async()=>{
  const wrapper=source.slice(source.indexOf('export default async function timedSoftWarmup')).replace('export default ','');
  let timer;let originalClosed=0;let sessionClosed=0;let timerCleared=false;
  const dedicated={close:async()=>{sessionClosed++;}};
  const original={close:async()=>{originalClosed++;},context:()=>({newPage:async()=>dedicated})};
  const sandbox={setTimeout:callback=>{timer=callback;return 1;},clearTimeout:()=>{timerCleared=true;},
    runWarmup:async ctx=>{assert.equal(ctx.page,dedicated);timer();}};
  const run=vm.runInNewContext(wrapper+'\ntimedSoftWarmup',sandbox);
  await run({page:original,inputs:{durationMinutes:20},log:()=>{}});
  assert.equal(originalClosed,0);assert.ok(sessionClosed>=1);assert.equal(timerCleared,true);
});
