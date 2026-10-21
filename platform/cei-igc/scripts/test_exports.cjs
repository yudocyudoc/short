/* Offline smoke test of serialization logic using an inert DOM stub. No network. */
const fs=require('fs');
const path=require('path');
const vm=require('vm');
const root=path.resolve(__dirname,'..');
const html=fs.readFileSync(path.join(root,'public/index.html'),'utf8');
const identifiers=[...html.matchAll(/\bid="([\w-]+)"/g)].map(x=>x[1]);
const elems=new Map();
const classList={add(){},remove(){},toggle(){}};
function element(id){if(!elems.has(id)){elems.set(id,{id,value:'',checked:false,textContent:'',innerHTML:'',classList,style:{},disabled:false,dataset:{},addEventListener(){},setAttribute(){},append(){},replaceChildren(){},querySelector(){return {textContent:'',classList}},querySelectorAll(){return []}})}return elems.get(id)}
for(const id of identifiers)element(id);
const document={getElementById:element,querySelectorAll(){return []},addEventListener(){},createElement(){return {className:'',textContent:'',append(){}}}};
const context={document,window:{scrollTo(){},clearTimeout(){},setTimeout(){return 1}},console,JSON,Date,Math,Number,String,Object,RegExp,URL,Blob,Array,Set};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(root,'public/app.js'),'utf8'),context,{filename:'app.js'});
vm.runInContext('readDemo()',context);
const intake=vm.runInContext('readIntake()',context);
const arena=vm.runInContext('readArena()',context);
if(intake.schema_version!=='igc.investigation_intake.v0.1'||intake.evidence.holdout.contents_included!==false)throw Error('Intake invariant');
if(intake.evidence.holdout.server_isolation_verified!==false)throw Error('False isolation claim');
if(arena.structure_proposals.length!==2||arena.assessment_parameter_proposals.length!==1)throw Error('Lane counts');
if(arena.structure_proposals.some(x=>x.validation.g1!=='NOT_RUN'))throw Error('Gate must not be approved by form');
if(arena.snapshot.holdout_contents_exposed!==false)throw Error('Reserve leaked');
if(JSON.stringify(arena).includes('holdout_values')||JSON.stringify(arena).includes('gold_label'))throw Error('Forbidden key');
if(arena.evaluation_plan.target_observable_ids.join(',')!=='ventas_hora,cola_minutos')throw Error('Observable IDs');
fs.writeFileSync(path.join(root,'examples/investigation_intake_demo.json'),JSON.stringify(intake,null,2)+'\n');
fs.writeFileSync(path.join(root,'examples/arena_input_demo.json'),JSON.stringify(arena,null,2)+'\n');
console.log('JS CONTRACTS: PASS (demo fixtures exported; no network or external models)');

