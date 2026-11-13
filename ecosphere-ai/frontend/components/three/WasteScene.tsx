'use client';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Text, Float } from '@react-three/drei';
import { useMemo } from 'react';
import * as THREE from 'three';
const colors=['#52e8ac','#24cad4','#acd966','#f4b96b','#b2a6f5'];
function Bottle({position,color,fill}:{position:[number,number,number];color:string;fill:number}){
 return <group position={position}><mesh position={[0,.32*fill,0]}><cylinderGeometry args={[.16,.19,.63*fill,9]}/><meshStandardMaterial color={color} transparent opacity={.74} metalness={.12} roughness={.26}/></mesh><mesh position={[0,.64*fill+.08,0]}><cylinderGeometry args={[.082,.092,.16,9]}/><meshStandardMaterial color={color} transparent opacity={.9}/></mesh><mesh position={[0,.64*fill+.18,0]}><cylinderGeometry args={[.10,.10,.05,9]}/><meshStandardMaterial color="#d5fff0" roughness={.35}/></mesh></group>
}
export default function WasteScene({data}:{data:{name:string;value:number}[]}){
 const top=data.slice(0,5);const scale=Math.max(.1,Math.ceil(Math.max(...top.map(x=>x.value),0)/8*10)/10);
 return <div className="waste-scene" aria-label="3D illustration of recorded waste by category, scaled to kilograms"><Canvas camera={{position:[8,7,10],fov:42}} dpr={[1,1.5]} gl={{antialias:false,powerPreference:'low-power'}}><color attach="background" args={['#0b2119']}/><ambientLight intensity={1.55}/><directionalLight position={[4,9,7]} intensity={2.5}/><pointLight position={[-3,6,4]} color="#53b99b" intensity={20}/><mesh rotation={[-Math.PI/2,0,0]} position={[0,-.05,0]}><planeGeometry args={[16,8]}/><meshStandardMaterial color="#102e22"/></mesh><gridHelper args={[15,15,'#2d6146','#214532']} position={[0,-.03,0]}/>{top.map((d,i)=>{const x=(i-(top.length-1)/2)*2.35;const count=Math.ceil(d.value/scale);return <group key={d.name}>{Array.from({length:count},(_,j)=><Bottle key={j} position={[x+((j%2)-.5)*.47,.01,((Math.floor(j/2))-1.5)*.55]} color={colors[i]} fill={Math.min(1,Math.max(.05,(d.value-j*scale)/scale))}/>)}<Text fontSize={.26} maxWidth={2.2} textAlign="center" color="#bdebd3" position={[x,.15,2.2]} rotation={[-Math.PI/2,0,0]}>{d.name}</Text><Text fontSize={.26} color={colors[i]} position={[x,1.65,0]}>{d.value.toFixed(2)} kg</Text></group>})}<OrbitControls enablePan={false} minDistance={8} maxDistance={21} maxPolarAngle={Math.PI/2.1}/></Canvas><span className="waste-scene-note">Each full 3D bottle shape represents {scale.toFixed(2)} kg of recorded plastic, not one physical bottle. Partial shapes show remaining mass.</span></div>
}
