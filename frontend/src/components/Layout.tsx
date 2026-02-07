import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { useAuth } from '@/store/AuthContext';
import { useTheme } from '@/store/ThemeContext';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Menu, X, MessageSquare } from 'lucide-react';
import ChatPanel from './ChatPanel';
import { Mascot } from './Mascots';

export default function Layout() {
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const getInitials = (name: string | null, email: string) => {
    if (name) {
      return name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2);
    }
    return email.slice(0, 2).toUpperCase();
  };

  const isInstructor = user?.role === 'instructor';

  return (
    <div className="min-h-screen bg-background">
      {/* Theme accent bar */}
      <div className="h-1 w-full bg-primary" />
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center">
          <Link to="/" className="mr-6 flex items-center space-x-2">
            <Mascot theme={theme} className="h-8 w-8" />
            <span className="hidden font-bold sm:inline-block text-primary">Quiz Builder</span>
          </Link>

          <nav className="hidden md:flex md:flex-1 md:items-center md:space-x-6">
            <Link to="/quizzes" className="text-sm font-medium transition-colors hover:text-primary">
              Browse Quizzes
            </Link>
            {isInstructor && (
              <>
                <Link
                  to="/my-quizzes"
                  className="text-sm font-medium transition-colors hover:text-primary"
                >
                  My Quizzes
                </Link>
                <Link
                  to="/quizzes/create"
                  className="text-sm font-medium transition-colors hover:text-primary"
                >
                  Create Quiz
                </Link>
              </>
            )}
            {!isInstructor && (
              <Link
                to="/my-attempts"
                className="text-sm font-medium transition-colors hover:text-primary"
              >
                My Attempts
              </Link>
            )}
          </nav>

          <div className="flex flex-1 items-center justify-end space-x-4">
            {isInstructor && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setChatOpen(true)}
                className="hidden md:flex"
              >
                <MessageSquare className="mr-2 h-4 w-4" />
                AI Assistant
              </Button>
            )}

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-primary text-primary-foreground">
                      {getInitials(user?.display_name || null, user?.email || '')}
                    </AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56" align="end" forceMount>
                <DropdownMenuLabel className="font-normal">
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium leading-none">
                      {user?.display_name || user?.email}
                    </p>
                    <p className="text-xs leading-none text-muted-foreground">
                      {user?.email}
                    </p>
                    <p className="text-xs leading-none text-muted-foreground capitalize">
                      {user?.role}
                    </p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuLabel className="text-xs text-muted-foreground">
                  Theme
                </DropdownMenuLabel>
                <DropdownMenuItem onClick={() => setTheme('byu')}>
                  <span
                    className={`mr-2 h-3 w-3 rounded-full ${
                      theme === 'byu' ? 'ring-2 ring-offset-2' : ''
                    }`}
                    style={{ backgroundColor: '#002E5D' }}
                  />
                  BYU (Blue)
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme('utah')}>
                  <span
                    className={`mr-2 h-3 w-3 rounded-full ${
                      theme === 'utah' ? 'ring-2 ring-offset-2' : ''
                    }`}
                    style={{ backgroundColor: '#CC0000' }}
                  />
                  Utah (Red)
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout}>Log out</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            <Button
              variant="ghost"
              className="md:hidden"
              size="sm"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
          </div>
        </div>

        {mobileMenuOpen && (
          <div className="border-t md:hidden">
            <nav className="flex flex-col space-y-2 p-4">
              <Link
                to="/quizzes"
                className="text-sm font-medium transition-colors hover:text-primary"
                onClick={() => setMobileMenuOpen(false)}
              >
                Browse Quizzes
              </Link>
              {isInstructor && (
                <>
                  <Link
                    to="/my-quizzes"
                    className="text-sm font-medium transition-colors hover:text-primary"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    My Quizzes
                  </Link>
                  <Link
                    to="/quizzes/create"
                    className="text-sm font-medium transition-colors hover:text-primary"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Create Quiz
                  </Link>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setChatOpen(true);
                      setMobileMenuOpen(false);
                    }}
                  >
                    <MessageSquare className="mr-2 h-4 w-4" />
                    AI Assistant
                  </Button>
                </>
              )}
              {!isInstructor && (
                <Link
                  to="/my-attempts"
                  className="text-sm font-medium transition-colors hover:text-primary"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  My Attempts
                </Link>
              )}
            </nav>
          </div>
        )}
      </header>

      <main className="container py-6">
        <Outlet />
      </main>

      {isInstructor && <ChatPanel open={chatOpen} onClose={() => setChatOpen(false)} theme={theme} />}
    </div>
  );
}
