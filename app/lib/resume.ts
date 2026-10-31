export const isResumeContent=(text:string)=>text.length>200||text.includes('简历');
export function forModel(text:string){return text
 .replace(/(?:姓名|身份证号?|住址|家庭地址|通讯地址|手机|电话|邮箱)\s*[:：][^\n。；;]*/g,'[个人信息已省略]')
 .replace(/[\w.+-]+@[\w.-]+\.[a-z]{2,}/gi,'[联系方式已省略]')
 .replace(/\d{17}[\dXx]|\d{11}/g,'[身份或联系方式已省略]');}
export function containsResumeEcho(reply:string,resume:string){const source=resume.replace(/\s+/g,'');const text=reply.replace(/\s+/g,'');for(let i=0;i<=text.length-16;i++)if(source.includes(text.slice(i,i+16)))return true;return false;}
