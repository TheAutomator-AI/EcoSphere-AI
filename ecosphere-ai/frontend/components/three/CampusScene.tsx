'use client';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Text, Float } from '@react-three/drei';
import { useMemo } from 'react';
import type { Zone } from '@/lib/types';
import * as THREE from 'three';
const placements:[[number,number,number],string][]=[ [[-4,0,-2],'Academic Block'], [[0,0,-3.5],'Library'], [[4,0,-2],'Cafeteria'],[[-4,0,2.4],'Hostel'], [[0,0,2],'Innovation Lab'], [[4,0,2.5],'Campus Garden'] ];
function Building({name,position,waste,max,thresholdLow,thresholdHigh,selected,onClick}:{name:string;position:[number,number,number];waste:number|null;max:number;thresholdLow:number;thresholdHigh:number;selected:boolean;onClick:()=>void}){
 const level=waste===null?'#4e786d':waste<thresholdLow?'#37d99b':waste<thresholdHigh?'#ecbc59':'#f6817a';
 const low=name.includes('Garden');const h=low?.16:name.includes('Hostel')?2.3:name.includes('Academic')?2.2:1.45;
 return <group position={position} onClick={e=>{e.stopPropagation();onClick()}}>
  <mesh position={[0,h/2,0]} castShadow><boxGeometry args={[2.25,h,1.8]}/><meshStandardMaterial color={selected?'#265d4d':'#173a31'} roughness={.72} metalness={.12}/></mesh>
  {!low&&<mesh position={[0,h+.08,0]}><boxGeometry args={[2.4,.15,2]}/><meshStandardMaterial color={level} emissive={level} emissiveIntensity={.16}/></mesh>}
  {!low&&Array.from({length:6},(_,i)=><mesh key={i} position={[-.72+(i%3)*.72,.55+Math.floor(i/3)*.77, .92]}><boxGeometry args={[.35,.4,.03]}/><meshBasicMaterial color="#6de4c5" transparent opacity={.45}/></mesh>)}
  <Float speed={1.4} floatIntensity={.12}><mesh position={[0,h+.65,0]}><sphereGeometry args={[.12,12,12]}/><meshBasicMaterial color={level}/></mesh></Float>
  <Text position={[0,.06,1.48]} rotation={[-Math.PI/2,0,0]} fontSize={.29} color="#c9fff0" maxWidth={3} anchorX="center">{name}</Text>
  {selected&&<mesh position={[0,.04,0]}><ringGeometry args={[1.58,1.68,64]}/><meshBasicMaterial color="#61edbb" side={THREE.DoubleSide}/></mesh>}
 </group>
}
function Tree({position}:{position:[number,number,number]}){return <group position={position}><mesh position={[0,.25,0]}><cylinderGeometry args={[.07,.11,.5,6]}/><meshStandardMaterial color="#7b6948"/></mesh><mesh position={[0,.9,0]}><coneGeometry args={[.57,1.35,7]}/><meshStandardMaterial color="#186f50"/></mesh></group>}
export default function CampusScene({zones,byZone,onSelect,selected}:{zones:Zone[];byZone:{name:string;value:number}[];onSelect:(name:string)=>void;selected:string|null}){
 const stats=useMemo(()=>new Map(byZone.map(z=>[z.name,z.value])),[byZone]);
 const shown=zones.length?zones.map((z,i)=>({z,pos:placements[i%6][0]})):placements.map(([pos,name],i)=>({z:{id:`placeholder-${i}`,name,kind:'building',threshold_low_kg:4,threshold_high_kg:12},pos}));
 return <div className="campus-scene"><Canvas shadows camera={{position:[11,11,13],fov:42}} dpr={[1,1.5]} gl={{antialias:false,powerPreference:'low-power'}}><color attach="background" args={['#081b18']}/><ambientLight intensity={1.5}/><directionalLight position={[8,12,6]} intensity={2.3} castShadow shadow-mapSize-width={1024} shadow-mapSize-height={1024}/><group><mesh rotation={[-Math.PI/2,0,0]} receiveShadow><planeGeometry args={[15.5,11.5]}/><meshStandardMaterial color="#0e3329"/></mesh><gridHelper args={[15,15,'#245d4b','#194338']} position={[0,.018,0]}/><mesh position={[0,.02,0]}><boxGeometry args={[.8,.03,11]}/><meshStandardMaterial color="#386a55"/></mesh><mesh position={[0,.02,0]}><boxGeometry args={[14,.03,.75]}/><meshStandardMaterial color="#386a55"/></mesh>{shown.map(({z,pos},i)=><Building key={z.id} name={z.name} position={pos} waste={stats.get(z.name)??null} max={20} thresholdLow={z.threshold_low_kg} thresholdHigh={z.threshold_high_kg} selected={selected===z.name} onClick={()=>onSelect(z.name)}/>)}{[[-6.4,-3.7],[-6,3.7],[6.3,3.8],[6.4,-3.8],[-2.4,4.6],[2.7,4.6],[-2.5,-4.5],[2.5,-4.5]].map(([x,z],i)=><Tree key={i} position={[x,0,z]}/>)}</group><OrbitControls enablePan={false} minDistance={10} maxDistance={28} maxPolarAngle={Math.PI/2.15} minPolarAngle={.42} autoRotate={false}/></Canvas><span className="twin-control">DRAG TO ORBIT · SCROLL TO ZOOM · SELECT A ZONE</span></div>
}
