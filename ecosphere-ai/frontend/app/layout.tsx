import type { Metadata } from 'next';
import './globals.css';
export const metadata:Metadata={title:'EcoSphere AI | Developed by Raja',description:'EcoSphere AI is an intelligent 3D campus plastic auditing and environmental sustainability platform developed by Raja.',authors:[{name:'Raja'}],keywords:['EcoSphere AI','Plastic-Free Campus','Sustainability','SDG 12','Environmental Audit','Raja'],openGraph:{title:'EcoSphere AI | Developed by Raja',description:'Intelligence for a Plastic-Free Tomorrow.',type:'website'}};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>}
