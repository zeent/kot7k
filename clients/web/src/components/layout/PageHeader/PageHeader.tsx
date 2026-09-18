import {
  Breadcrumb,
  BreadcrumbItem,
} from "@carbon/react";
import "./PageHeader.scss";

export interface PageBreadcrumb {
  label: string;
  href?: string;
}

export interface PageHeaderProps {
  title: string;
  subtitle?: React.ReactNode;
  breadcrumbs?: PageBreadcrumb[];
  actions?: React.ReactNode;
}

export default function PageHeader({
  title,
  subtitle,
  breadcrumbs,
  actions,
}: PageHeaderProps) {
  return (
    <header className="page-header">
      <div className="page-header__inner">
        {breadcrumbs && breadcrumbs.length > 0 && (
          <div className="page-header__breadcrumbs">
            <Breadcrumb noTrailingSlash>
              {breadcrumbs.map((item, index) => {
                const isLast = index === breadcrumbs.length - 1;

                return isLast ? (
                  <BreadcrumbItem
                    key={index}
                    isCurrentPage
                  >
                    {item.label}
                  </BreadcrumbItem>
                ) : (
                  <BreadcrumbItem
                    key={index}
                    href={item.href}
                  >
                    {item.label}
                  </BreadcrumbItem>
                );
              })}
            </Breadcrumb>
          </div>
        )}

        <div className="page-header__content">
          <div className="page-header__titles">
            <h1 className="page-header__title">
              {title}
            </h1>

            {subtitle && (
              <p className="page-header__subtitle">
                {subtitle}
              </p>
            )}
          </div>

          {actions && (
            <div className="page-header__actions">
              {actions}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}