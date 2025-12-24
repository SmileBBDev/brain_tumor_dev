import { Link } from 'react-router-dom';
import useBreadcrumb  from '../hooks/useBreadcrumb';
import type { Role } from '@/types/role';

interface Props {
   role : Role;
}

export default function Breadcrumbs({role}: Props){
    const breadcrumb = useBreadcrumb(role);

    if (breadcrumb.length <= 0) return null;

    return (
        <nav className='breadcrumb'>
            {breadcrumb.map((item,idx) =>{
                const isLast = idx === breadcrumb.length - 1;

                return (
                    <span key={item.id}>
                        {!isLast && item.path?(
                            <Link to={item.path}>{item.label}</Link>
                        ):(
                            <span>{item.label}</span>
                        )} 
                        {!isLast && <span className='sep'>&gt;</span>}
                    </span>
                )
            })}
        </nav>
    )
}