const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000/api';
export function getToken(){ return localStorage.getItem('learnai_token') || ''; }
export function setToken(token){ if(token) localStorage.setItem('learnai_token',token); else localStorage.removeItem('learnai_token'); }
export async function api(path, options={}) {
  const headers={'Content-Type':'application/json', ...(options.headers||{})};
  const token=getToken(); if(token) headers.Authorization=`Bearer ${token}`;
  let response;
  try { response=await fetch(`${API_BASE}${path}`,{...options,headers}); }
  catch { throw new Error('Cannot connect to backend. Start Flask in the backend terminal (python app.py).'); }
  const data=await response.json().catch(()=>({}));
  if(!response.ok) throw new Error(data.error || `Request failed (${response.status}).`);
  return data;
}
