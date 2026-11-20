import Image from 'next/image';

export function BrandLogo() {
  return (
    <span className="brand-logo" aria-hidden="true">
      <Image src="/ignidi-labs.jpeg" alt="" width={1600} height={1600} unoptimized />
    </span>
  );
}
