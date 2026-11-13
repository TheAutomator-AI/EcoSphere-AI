'use client';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Stars } from '@react-three/drei';
import { useEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';

const continents=[
 [[-170,65],[-140,72],[-116,62],[-103,54],[-80,50],[-70,43],[-82,25],[-98,16],[-110,30],[-126,37],[-135,50]],
 [[-81,13],[-66,9],[-52,-1],[-49,-16],[-61,-34],[-73,-56],[-79,-38],[-72,-20]],
 [[-11,36],[6,37],[18,30],[34,30],[43,11],[49,-12],[35,-33],[18,-35],[11,-19],[-4,5],[-17,20]],
 [[-10,36],[-3,59],[18,70],[43,63],[68,70],[91,58],[122,55],[141,47],[156,55],[171,42],[143,22],[123,10],[102,0],[89,20],[71,10],[54,27],[33,34],[19,44],[6,47]],
 [[113,-13],[135,-10],[151,-20],[154,-38],[133,-41],[114,-32]],
 [[-50,82],[-34,83],[-43,59],[-59,60]],
 [[-180,-66],[-140,-71],[-90,-69],[-35,-75],[25,-68],[90,-74],[145,-69],[180,-66],[180,-90],[-180,-90]]
];
function earthTexture(){
 const canvas=document.createElement('canvas');canvas.width=2048;canvas.height=1024;const ctx=canvas.getContext('2d')!;
 const sea=ctx.createLinearGradient(0,0,0,1024);sea.addColorStop(0,'#041923');sea.addColorStop(.53,'#07394a');sea.addColorStop(1,'#051a27');ctx.fillStyle=sea;ctx.fillRect(0,0,2048,1024);
 for(let i=0;i<2600;i++){const x=(i*997.7)%2048,y=(i*457.3)%1024;const a=.03+(i%8)/400;ctx.fillStyle=`rgba(45,183,196,${a})`;ctx.fillRect(x,y,2+(i%3),1)}
 const xy=([lon,lat]:number[])=>[(lon+180)/360*2048,(90-lat)/180*1024];
 continents.forEach((shape,index)=>{ctx.beginPath();shape.forEach((p,i)=>{const [x,y]=xy(p);i===0?ctx.moveTo(x,y):ctx.lineTo(x,y)});ctx.closePath();ctx.fillStyle=index===6?'#a9bbad':'#174e44';ctx.fill();ctx.strokeStyle='#35997c';ctx.lineWidth=3;ctx.stroke();});
 // Land texture freckles; clipped in rough continent regions via pixel sampling of green channel.
 const data=ctx.getImageData(0,0,2048,1024);for(let i=0;i<9000;i++){const x=Math.floor((i*1129.3)%2048),y=Math.floor((i*791.17)%1024),idx=(y*2048+x)*4;if(data.data[idx+1]>62&&data.data[idx]<55){ctx.fillStyle=i%9?'rgba(121,218,143,.17)':'rgba(202,243,140,.34)';ctx.fillRect(x,y,1+(i%4),1+(i%3));}}
 // Night-light accents are decorative, not actual geolocated monitoring points.
 for(const [lo,la] of [[-74,41],[2,49],[78,22],[122,32],[139,36],[30,31],[-1,52],[12,43],[103,1]]){const [x,y]=xy([lo,la]);const g=ctx.createRadialGradient(x,y,0,x,y,16);g.addColorStop(0,'rgba(144,246,174,.85)');g.addColorStop(1,'rgba(144,246,174,0)');ctx.fillStyle=g;ctx.fillRect(x-16,y-16,32,32)}
 const texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;texture.anisotropy=4;return texture;
}
function Globe(){const group=useRef<THREE.Group>(null);const mat=useMemo(()=>typeof document!=='undefined'?earthTexture():null,[]);const {pointer}=useThree();useFrame((_,delta)=>{if(!group.current)return;group.current.rotation.y+=delta*.047;group.current.rotation.x=THREE.MathUtils.lerp(group.current.rotation.x,-pointer.y*.10,.018);group.current.rotation.z=THREE.MathUtils.lerp(group.current.rotation.z,pointer.x*.04,.018)});useEffect(()=>()=>mat?.dispose(),[mat]);return <group ref={group} rotation={[.17,-.35,-.1]}><mesh><sphereGeometry args={[2.12,72,72]}/><meshStandardMaterial map={mat} metalness={.08} roughness={.84} emissive="#064b41" emissiveIntensity={.21}/></mesh><mesh><sphereGeometry args={[2.16,64,64]}/><shaderMaterial transparent depthWrite={false} blending={THREE.AdditiveBlending} uniforms={{glowColor:{value:new THREE.Color('#28cda8')}}} vertexShader={`varying vec3 vNormal;varying vec3 vPosition;void main(){vNormal=normalize(normalMatrix*normal);vPosition=vec3(modelViewMatrix*vec4(position,1.0));gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`} fragmentShader={`varying vec3 vNormal;varying vec3 vPosition;uniform vec3 glowColor;void main(){float rim=pow(1.0-abs(dot(normalize(vNormal),normalize(-vPosition))),3.5);gl_FragColor=vec4(glowColor,rim*.40);}`}/></mesh><mesh rotation={[.2,-.5,.12]}><torusGeometry args={[2.48,.003,4,180]}/><meshBasicMaterial color="#1e8b7b" transparent opacity={.65}/></mesh></group>}
export default function EarthScene(){return <div className="earth-canvas" aria-label="Decorative animated 3D Earth"><Canvas camera={{position:[0,0,7.1],fov:45}} dpr={[1,1.6]} gl={{antialias:false,alpha:true,powerPreference:'low-power'}}><ambientLight intensity={.52}/><directionalLight position={[5,4,5]} color="#a7fff0" intensity={2.5}/><pointLight position={[-5,-1,2]} color="#2adfc7" intensity={15}/><Stars radius={65} depth={20} count={500} factor={1.8} fade speed={.25}/><Globe/></Canvas><div className="earth-axis-label earth-axis-label-top"><span className="label-dot"/> PLANETARY INTELLIGENCE</div><div className="earth-axis-label earth-axis-label-bottom">01 / EARTH OBSERVATION <span>◦</span> 3D EXPERIENCE</div></div>}
