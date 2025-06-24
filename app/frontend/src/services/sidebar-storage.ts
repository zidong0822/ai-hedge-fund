export interface SidebarStates {
  leftCollapsed: boolean;
  rightCollapsed: boolean;
}

export class SidebarStorageService {
  private static readonly LEFT_SIDEBAR_KEY = 'ai-hedge-fund-left-sidebar-collapsed';
  private static readonly RIGHT_SIDEBAR_KEY = 'ai-hedge-fund-right-sidebar-collapsed';

  /**
   * Save left sidebar collapsed state to localStorage
   */
  static saveLeftSidebarState(isCollapsed: boolean): boolean {
    try {
      localStorage.setItem(this.LEFT_SIDEBAR_KEY, JSON.stringify(isCollapsed));
      return true;
    } catch (error) {
      console.error('Failed to save left sidebar state to localStorage:', error);
      return false;
    }
  }

  /**
   * Save right sidebar collapsed state to localStorage
   */
  static saveRightSidebarState(isCollapsed: boolean): boolean {
    try {
      localStorage.setItem(this.RIGHT_SIDEBAR_KEY, JSON.stringify(isCollapsed));
      return true;
    } catch (error) {
      console.error('Failed to save right sidebar state to localStorage:', error);
      return false;
    }
  }

  /**
   * Save both sidebar states to localStorage
   */
  static saveSidebarStates(states: SidebarStates): boolean {
    try {
      const leftSuccess = this.saveLeftSidebarState(states.leftCollapsed);
      const rightSuccess = this.saveRightSidebarState(states.rightCollapsed);
      return leftSuccess && rightSuccess;
    } catch (error) {
      console.error('Failed to save sidebar states to localStorage:', error);
      return false;
    }
  }

  /**
   * Load left sidebar collapsed state from localStorage
   */
  static loadLeftSidebarState(defaultValue: boolean = true): boolean {
    try {
      const saved = localStorage.getItem(this.LEFT_SIDEBAR_KEY);
      if (saved === null) {
        return defaultValue;
      }
      
      const parsed = JSON.parse(saved);
      return typeof parsed === 'boolean' ? parsed : defaultValue;
    } catch (error) {
      console.error('Failed to load left sidebar state from localStorage:', error);
      return defaultValue;
    }
  }

  /**
   * Load right sidebar collapsed state from localStorage
   */
  static loadRightSidebarState(defaultValue: boolean = true): boolean {
    try {
      const saved = localStorage.getItem(this.RIGHT_SIDEBAR_KEY);
      if (saved === null) {
        return defaultValue;
      }
      
      const parsed = JSON.parse(saved);
      return typeof parsed === 'boolean' ? parsed : defaultValue;
    } catch (error) {
      console.error('Failed to load right sidebar state from localStorage:', error);
      return defaultValue;
    }
  }

  /**
   * Load both sidebar states from localStorage
   */
  static loadSidebarStates(defaultStates: SidebarStates = { leftCollapsed: true, rightCollapsed: true }): SidebarStates {
    return {
      leftCollapsed: this.loadLeftSidebarState(defaultStates.leftCollapsed),
      rightCollapsed: this.loadRightSidebarState(defaultStates.rightCollapsed),
    };
  }

  /**
   * Clear left sidebar state from localStorage
   */
  static clearLeftSidebarState(): boolean {
    try {
      localStorage.removeItem(this.LEFT_SIDEBAR_KEY);
      return true;
    } catch (error) {
      console.error('Failed to clear left sidebar state from localStorage:', error);
      return false;
    }
  }

  /**
   * Clear right sidebar state from localStorage
   */
  static clearRightSidebarState(): boolean {
    try {
      localStorage.removeItem(this.RIGHT_SIDEBAR_KEY);
      return true;
    } catch (error) {
      console.error('Failed to clear right sidebar state from localStorage:', error);
      return false;
    }
  }

  /**
   * Clear both sidebar states from localStorage
   */
  static clearSidebarStates(): boolean {
    try {
      const leftSuccess = this.clearLeftSidebarState();
      const rightSuccess = this.clearRightSidebarState();
      return leftSuccess && rightSuccess;
    } catch (error) {
      console.error('Failed to clear sidebar states from localStorage:', error);
      return false;
    }
  }

  /**
   * Check if left sidebar state exists in localStorage
   */
  static hasLeftSidebarState(): boolean {
    try {
      return localStorage.getItem(this.LEFT_SIDEBAR_KEY) !== null;
    } catch (error) {
      console.error('Failed to check left sidebar state existence in localStorage:', error);
      return false;
    }
  }

  /**
   * Check if right sidebar state exists in localStorage
   */
  static hasRightSidebarState(): boolean {
    try {
      return localStorage.getItem(this.RIGHT_SIDEBAR_KEY) !== null;
    } catch (error) {
      console.error('Failed to check right sidebar state existence in localStorage:', error);
      return false;
    }
  }

  /**
   * Check if both sidebar states exist in localStorage
   */
  static hasSidebarStates(): { left: boolean; right: boolean } {
    return {
      left: this.hasLeftSidebarState(),
      right: this.hasRightSidebarState(),
    };
  }
} 