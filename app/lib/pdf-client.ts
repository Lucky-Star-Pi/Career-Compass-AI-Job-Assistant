export const PDF_LIMITS={bytes:5*1024*1024,pages:5,characters:6000,minimum:50};
export function pdfInputError(file:{name:string;size:number}){if(!/\.pdf$/i.test(file.name))return '请选择 PDF 文件';if(file.size>PDF_LIMITS.bytes)return 'PDF 文件不能超过 5MB，请压缩后重试或粘贴文本';return null;}
export async function extractPdf(file:File):Promise<string>{
 const error=pdfInputError(file);if(error)throw new Error(error);
 let task:{destroy:()=>Promise<void>}|undefined;
 try{
 const [pdf,handler]=await Promise.all([import('pdfjs-dist/legacy/build/pdf.mjs'),import('pdfjs-dist/legacy/build/pdf.worker.mjs')]);
 // Register the handler in this window: PDF.js selects its in-thread fake worker,
 // never constructing a browser Worker or sending the document to a server.
 (globalThis as typeof globalThis & {pdfjsWorker?:{WorkerMessageHandler:unknown}}).pdfjsWorker={WorkerMessageHandler:handler.WorkerMessageHandler};
 const loading=pdf.getDocument({data:new Uint8Array(await file.arrayBuffer()),useWorkerFetch:false,isEvalSupported:false,disableFontFace:true,verbosity:0});
 task=loading;
  const document=await loading.promise;let text='';
  for(let number=1;number<=Math.min(PDF_LIMITS.pages,document.numPages)&&text.length<PDF_LIMITS.characters;number++){
   const page=await document.getPage(number);const content=await page.getTextContent();
   for(const item of content.items)if('str' in item){text+=(item.str+(item.hasEOL?'\n':' '));if(text.length>=PDF_LIMITS.characters)break;}
   page.cleanup();text+='\n';
  }
  text=text.trim().slice(0,PDF_LIMITS.characters);
  if(text.replace(/\s/g,'').length<PDF_LIMITS.minimum)throw new Error('这份 PDF 没读到文字，可能是扫描件，请改为粘贴文本');
  return text;
 }catch{throw new Error('这份 PDF 没读到文字，可能是扫描件，请改为粘贴文本');}
 finally{await task?.destroy().catch(()=>{});}
}
