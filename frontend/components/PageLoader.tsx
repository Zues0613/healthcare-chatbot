export default function PageLoader() {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/95 backdrop-blur-sm">
      <div className="relative">
        {/* Animated gradient background */}
        <div className="absolute inset-0 rounded-full bg-gradient-to-br from-emerald-500/20 via-green-500/20 to-teal-500/20 blur-2xl animate-pulse" />
        
        {/* Spinner */}
        <div className="relative flex flex-col items-center gap-4">
          <div className="relative h-16 w-16">
            <div className="absolute inset-0 rounded-full border-4 border-emerald-500/20" />
            <div className="absolute inset-0 animate-spin rounded-full border-4 border-transparent border-t-emerald-500 border-r-green-500" />
            <div className="absolute inset-2 animate-spin rounded-full border-4 border-transparent border-t-teal-500 border-r-emerald-500" style={{ animationDirection: 'reverse', animationDuration: '0.8s' }} />
          </div>
          
          {/* Logo */}
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-emerald-500 via-green-500 to-teal-500 text-lg font-semibold text-white shadow-[0_15px_35px_rgba(16,185,129,0.35)]">
            HC
          </div>
          
          {/* Loading text */}
          <p className="text-sm font-medium text-emerald-300/80 animate-pulse">
            Loading...
          </p>
        </div>
      </div>
    </div>
  );
}

