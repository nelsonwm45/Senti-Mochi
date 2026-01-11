'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ChevronRight, Home } from 'lucide-react';
import { cn } from '@/lib/utils';

interface BreadcrumbItem {
  label: string;
  href: string;
}

// Map path segments to readable labels
const pathLabels: Record<string, string> = {
  dashboard: 'Dashboard',
  chat: 'Chat',
  documents: 'Documents',
  profile: 'Profile',
  settings: 'Settings',
  login: 'Login',
  signup: 'Sign Up',
};

export function Breadcrumbs() {
  const pathname = usePathname();

  // Generate breadcrumb items from pathname
  const generateBreadcrumbs = (): BreadcrumbItem[] => {
    const segments = pathname.split('/').filter(Boolean);

    if (segments.length === 0) {
      return [{ label: 'Home', href: '/' }];
    }

    const breadcrumbs: BreadcrumbItem[] = [];
    let currentPath = '';

    segments.forEach((segment, index) => {
      currentPath += `/${segment}`;

      // Skip auth group segments
      if (segment.startsWith('(') && segment.endsWith(')')) {
        return;
      }

      const label = pathLabels[segment] || segment.charAt(0).toUpperCase() + segment.slice(1);
      breadcrumbs.push({
        label,
        href: currentPath,
      });
    });

    return breadcrumbs;
  };

  const breadcrumbs = generateBreadcrumbs();

  if (breadcrumbs.length <= 1) {
    return (
      <h1 className="text-lg font-semibold text-foreground">
        {breadcrumbs[0]?.label || 'Home'}
      </h1>
    );
  }

  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1">
      <Link
        href="/dashboard"
        className="flex items-center text-foreground-muted hover:text-accent transition-colors"
        aria-label="Home"
      >
        <Home size={18} />
      </Link>

      {breadcrumbs.map((item, index) => {
        const isLast = index === breadcrumbs.length - 1;

        return (
          <div key={item.href} className="flex items-center gap-1">
            <ChevronRight size={16} className="text-foreground-muted" />
            {isLast ? (
              <span className="text-sm font-medium text-foreground">{item.label}</span>
            ) : (
              <Link
                href={item.href}
                className={cn(
                  'text-sm text-foreground-muted',
                  'hover:text-accent transition-colors'
                )}
              >
                {item.label}
              </Link>
            )}
          </div>
        );
      })}
    </nav>
  );
}

export default Breadcrumbs;
