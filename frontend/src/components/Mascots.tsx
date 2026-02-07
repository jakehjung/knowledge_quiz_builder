import { cn } from '@/lib/utils';

interface MascotProps {
  className?: string;
}

// BYU Cosmo the Cougar - Fierce tan cougar with blue accents
export function CougarMascot({ className }: MascotProps) {
  return (
    <svg
      viewBox="0 0 100 100"
      className={cn(className)}
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Background circle */}
      <circle cx="50" cy="50" r="48" fill="#002E5D" />

      {/* Cougar face - tan/brown */}
      <ellipse cx="50" cy="52" rx="32" ry="35" fill="#C4A574" />

      {/* Inner face - lighter */}
      <ellipse cx="50" cy="58" rx="22" ry="24" fill="#D4B896" />

      {/* Ears */}
      <path d="M22 28 L28 12 L38 30 Z" fill="#C4A574" stroke="#8B6914" strokeWidth="1" />
      <path d="M78 28 L72 12 L62 30 Z" fill="#C4A574" stroke="#8B6914" strokeWidth="1" />
      <path d="M26 26 L30 16 L36 28 Z" fill="#D4B896" />
      <path d="M74 26 L70 16 L64 28 Z" fill="#D4B896" />

      {/* Brow/angry eyebrows */}
      <path d="M25 38 L42 42 L42 38 L25 32 Z" fill="#002E5D" />
      <path d="M75 38 L58 42 L58 38 L75 32 Z" fill="#002E5D" />

      {/* Eyes - fierce blue */}
      <ellipse cx="35" cy="45" rx="8" ry="9" fill="white" />
      <ellipse cx="65" cy="45" rx="8" ry="9" fill="white" />
      <circle cx="36" cy="46" r="5" fill="#002E5D" />
      <circle cx="66" cy="46" r="5" fill="#002E5D" />
      <circle cx="37" cy="44" r="2" fill="white" />
      <circle cx="67" cy="44" r="2" fill="white" />

      {/* Nose */}
      <ellipse cx="50" cy="62" rx="6" ry="4" fill="#1a1a1a" />

      {/* Muzzle lines */}
      <path d="M50 66 L50 72" stroke="#8B6914" strokeWidth="2" />
      <path d="M44 70 Q50 76 56 70" stroke="#8B6914" strokeWidth="2" fill="none" />

      {/* Mouth - snarling */}
      <path d="M35 75 Q50 85 65 75" stroke="#1a1a1a" strokeWidth="2" fill="none" />

      {/* Fangs */}
      <path d="M40 75 L42 82 L44 75" fill="white" />
      <path d="M56 75 L58 82 L60 75" fill="white" />

      {/* Whisker spots */}
      <circle cx="30" cy="60" r="2" fill="#8B6914" />
      <circle cx="32" cy="66" r="2" fill="#8B6914" />
      <circle cx="70" cy="60" r="2" fill="#8B6914" />
      <circle cx="68" cy="66" r="2" fill="#8B6914" />

      {/* Fur details on cheeks */}
      <path d="M18 50 L25 52 M18 55 L24 56 M18 60 L24 60" stroke="#C4A574" strokeWidth="2" />
      <path d="M82 50 L75 52 M82 55 L76 56 M82 60 L76 60" stroke="#C4A574" strokeWidth="2" />
    </svg>
  );
}

// Utah Swoop - Fierce red hawk
export function HawkMascot({ className }: MascotProps) {
  return (
    <svg
      viewBox="0 0 100 100"
      className={cn(className)}
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Background circle */}
      <circle cx="50" cy="50" r="48" fill="#CC0000" />

      {/* Head feathers - dark red */}
      <ellipse cx="50" cy="48" rx="35" ry="38" fill="#8B0000" />

      {/* Face feathers - red */}
      <ellipse cx="50" cy="52" rx="28" ry="32" fill="#CC0000" />

      {/* Head crest feathers */}
      <path d="M30 8 L35 28 L25 20 Z" fill="#8B0000" />
      <path d="M42 5 L44 25 L36 18 Z" fill="#8B0000" />
      <path d="M50 3 L50 23 L44 15 Z" fill="#CC0000" />
      <path d="M58 5 L56 25 L64 18 Z" fill="#8B0000" />
      <path d="M70 8 L65 28 L75 20 Z" fill="#8B0000" />

      {/* White face markings */}
      <path d="M35 40 Q50 35 65 40 L60 55 Q50 52 40 55 Z" fill="#F5F5DC" />

      {/* Angry brow */}
      <path d="M25 38 L40 44 L40 40 L25 30 Z" fill="#5C0000" />
      <path d="M75 38 L60 44 L60 40 L75 30 Z" fill="#5C0000" />

      {/* Eyes - fierce */}
      <ellipse cx="38" cy="47" rx="7" ry="8" fill="white" />
      <ellipse cx="62" cy="47" rx="7" ry="8" fill="white" />
      <circle cx="39" cy="48" r="4" fill="#CC0000" />
      <circle cx="63" cy="48" r="4" fill="#CC0000" />
      <circle cx="38" cy="47" r="2" fill="black" />
      <circle cx="62" cy="47" r="2" fill="black" />
      <circle cx="37" cy="46" r="1" fill="white" />
      <circle cx="61" cy="46" r="1" fill="white" />

      {/* Beak - orange/yellow */}
      <path d="M50 52 L38 58 L50 80 L62 58 Z" fill="#FF8C00" />
      <path d="M50 52 L42 57 L50 75 L58 57 Z" fill="#FFA500" />
      {/* Beak detail line */}
      <path d="M50 55 L50 70" stroke="#CC6600" strokeWidth="1" />
      {/* Beak nostril */}
      <ellipse cx="46" cy="60" rx="2" ry="1" fill="#CC6600" />
      <ellipse cx="54" cy="60" rx="2" ry="1" fill="#CC6600" />

      {/* Feather details on sides */}
      <path d="M15 45 L22 48 M15 52 L22 54 M15 59 L22 60" stroke="#8B0000" strokeWidth="3" />
      <path d="M85 45 L78 48 M85 52 L78 54 M85 59 L78 60" stroke="#8B0000" strokeWidth="3" />

      {/* Wing feather hints */}
      <path d="M12 65 L20 55 L18 68 Z" fill="#8B0000" />
      <path d="M88 65 L80 55 L82 68 Z" fill="#8B0000" />
    </svg>
  );
}

// Combined mascot component that switches based on theme
export function Mascot({ theme, className }: { theme: 'byu' | 'utah'; className?: string }) {
  return theme === 'byu' ? (
    <CougarMascot className={className} />
  ) : (
    <HawkMascot className={className} />
  );
}
