const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const html=fs.readFileSync('index.html','utf8');
const engine=html.match(/<script>([\s\S]*?)<\/script>/)[1];
const context={module:{exports:{}}};vm.runInNewContext(engine,context);
const {diagnose}=context.module.exports;
const js=html.match(/<script>\n([\s\S]*)<\/script>/)[1];
const m=js.match(/const sample=([\s\S]*?);\nlet last/);
const base=vm.runInNewContext('('+m[1]+')');
const copy=()=>JSON.parse(JSON.stringify(base));
let count=0;function test(name,fn){fn();count++;console.log('PASS '+name);}
test('sample movement reconciles',()=>{const r=diagnose(copy());assert.equal(r.delta,-60000);assert.equal(r.rate,-.375);assert(r.alert);assert(Math.abs(r.residual)<1e-8);assert.equal(r.hypotheses[0].causal_effect,null);for(const v of Object.values(r.contributions))assert.equal(v.reduce((s,x)=>s+x.delta,0),r.delta);});
test('no evidence never invents causes',()=>{const d=copy();d.evidence=[];assert.equal(diagnose(d).hypotheses.length,0);});
test('incomplete, stale, duplicate, negative, null, mismatch, unequal periods block',()=>{
 for(const mutate of [d=>d.meta.complete=false,d=>d.meta.as_of='2026-08-23T13:00:00+08:00',d=>d.rows.push(d.rows[0]),d=>d.rows[0].gmv=-1,d=>d.rows[0].gmv=null,d=>d.meta.control_current++,d=>d.meta.current_end='2026-08-23T12:00:00+08:00']){const d=copy();mutate(d);assert.equal(diagnose(d).status,'blocked');}
});
test('normal and threshold response',()=>{const d=copy();d.config={relative:.5,absolute:5000};assert(!diagnose(d).alert);d.config.relative=.2;assert(diagnose(d).alert);});
test('zero baseline does not fabricate percent',()=>{const d=copy();d.rows.forEach(r=>{r.base_gmv=0;r.base_orders=0;});d.meta.control_baseline=0;const r=diagnose(d);assert.equal(r.rate,null);assert.equal(r.residual,null);assert(!r.alert);});
test('opposing changes preserved',()=>{const d=copy();d.rows[1].gmv=110000;d.meta.control_current=170000;const r=diagnose(d);assert.equal(r.delta,10000);assert(r.contributions.channel.some(c=>c.share<0));assert(r.contributions.channel.some(c=>c.share>1));});
test('out of window, unknown and malformed evidence excluded',()=>{const d=copy();d.evidence[0].at='2026-08-22T10:12:00+08:00';d.evidence.push(null);assert.equal(diagnose(d).hypotheses.length,0);});
test('100 independently computed decompositions reconcile',()=>{for(let i=1;i<=100;i++){const d=copy();d.rows[0].gmv=500+i*720;d.rows[0].orders=10+i;d.meta.control_current=d.rows.reduce((s,r)=>s+r.gmv,0);const r=diagnose(d);assert(Math.abs(r.residual)<1e-7);const [o,p]=r.factors;assert(Math.abs(o.current*p.current-r.current)<1e-7);}});
console.log(count+' test groups passed');

