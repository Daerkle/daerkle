'use client';

import Chart from '@/components/Chart';
import PivotLevels from '@/components/PivotLevels';
import SetupList from '@/components/SetupList';
import Watchlist from '@/components/Watchlist';
import { SymbolProvider, useSymbol } from '@/contexts/SymbolContext';
import { SidebarProvider, useSidebar } from '@/contexts/SidebarContext';

function BurgerButton() {
  const { toggle, isOpen } = useSidebar();
  
  return (
    <button
      onClick={toggle}
      className="fixed top-2 right-2 z-50 p-2 rounded bg-white shadow-lg md:hidden"
    >
      <div className="w-5 h-4 relative">
        <span className={`absolute w-full h-0.5 bg-gray-600 transform transition-all ${
          isOpen ? 'rotate-45 top-2' : 'top-0'
        }`} />
        <span className={`absolute w-full h-0.5 bg-gray-600 top-[7px] transition-opacity ${
          isOpen ? 'opacity-0' : 'opacity-100'
        }`} />
        <span className={`absolute w-full h-0.5 bg-gray-600 transform transition-all ${
          isOpen ? '-rotate-45 top-2' : 'top-[14px]'
        }`} />
      </div>
    </button>
  );
}

function MainContent() {
  const { selectedSymbol, setSelectedSymbol } = useSymbol();
  const { isOpen, toggle } = useSidebar();

  return (
    <div className="h-screen bg-gray-50 p-2">
      {/* Mobile Watchlist Overlay */}
      <div className={`
        fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity md:hidden
        ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}
      `} />
      
      <div className="h-full flex">
        {/* Main Content Area */}
        <div className="flex-1 grid grid-rows-[60%_40%] gap-2">
          {/* Chart und Pivot Levels */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
            <div className="md:col-span-2 bg-white rounded-lg shadow p-2">
              <Chart />
            </div>
            <div className="bg-white rounded-lg shadow p-2">
              <h2 className="text-sm font-semibold mb-1">Pivot Levels</h2>
              <div className="h-[calc(100%-1.5rem)]">
                {selectedSymbol ? (
                  <PivotLevels symbol={selectedSymbol} />
                ) : (
                  <div className="text-gray-500 text-xs">
                    Wählen Sie ein Symbol aus der Watchlist
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Setups */}
          <div className="bg-white rounded-lg shadow p-2">
            <h2 className="text-sm font-semibold mb-1">Setups</h2>
            <div className="h-[calc(100%-1.5rem)] overflow-auto">
              {selectedSymbol ? (
                <SetupList symbol={selectedSymbol} />
              ) : (
                <div className="text-gray-500 text-xs">
                  Wählen Sie ein Symbol aus der Watchlist
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Watchlist - Mobile: Sliding Sidebar, Desktop: Fixed Column */}
        <div className={`
          fixed md:static top-0 right-0 h-full w-64 bg-white shadow-lg z-40 
          transform transition-transform md:transform-none md:translate-x-0
          ${isOpen ? 'translate-x-0' : 'translate-x-full'}
          p-2
        `}>
          <Watchlist onSymbolSelect={setSelectedSymbol} selectedSymbol={selectedSymbol} />
        </div>

        {/* Mobile Overlay */}
        <div 
          className={`
            fixed inset-0 bg-black bg-opacity-50 z-30 md:hidden
            ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}
          `}
          onClick={toggle}
        />
      </div>

      {/* Burger Menu Button */}
      <button
        onClick={toggle}
        className="fixed top-2 right-2 z-50 p-2 rounded bg-white shadow-lg md:hidden"
      >
        <div className="w-5 h-4 relative">
          <span className={`absolute w-full h-0.5 bg-gray-600 transform transition-all ${
            isOpen ? 'rotate-45 top-2' : 'top-0'
          }`} />
          <span className={`absolute w-full h-0.5 bg-gray-600 top-[7px] transition-opacity ${
            isOpen ? 'opacity-0' : 'opacity-100'
          }`} />
          <span className={`absolute w-full h-0.5 bg-gray-600 transform transition-all ${
            isOpen ? '-rotate-45 top-2' : 'top-[14px]'
          }`} />
        </div>
      </button>
    </div>
  );
}

export default function Home() {
  return (
    <SymbolProvider>
      <SidebarProvider>
        <MainContent />
      </SidebarProvider>
    </SymbolProvider>
  );
}
