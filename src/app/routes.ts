import { createBrowserRouter } from 'react-router';
import { Layout } from './components/Layout';
import { Home } from './pages/Home';
import { Messenger } from './pages/Messenger';
import { Dashboard } from './pages/Dashboard';
import { OrganizationChart as Organization } from './components/OrganizationChart';
import { Tasks } from './pages/Tasks';
import { Deliverables } from './pages/Deliverables';
import { Meetings } from './pages/Meetings';
import { Attendance } from './pages/Attendance';
import { Announcements } from './pages/Announcements';
import { System } from './pages/System';
import { Settings } from './pages/Settings';
import { Profile } from './pages/Profile';

export const router = createBrowserRouter([
    {
        path: '/',
        Component: Layout,
        children: [
            { index: true, Component: Home },
            { path: 'dashboard', Component: Dashboard },
            { path: 'messenger', Component: Messenger },
            { path: 'messenger/:employeeId', Component: Messenger },
            { path: 'organization', Component: Organization },
            { path: 'tasks', Component: Tasks },
            { path: 'deliverables', Component: Deliverables },
            { path: 'meetings', Component: Meetings },
            { path: 'attendance', Component: Attendance },
            { path: 'announcements', Component: Announcements },
            { path: 'system', Component: System },
            { path: 'settings', Component: Settings },
            { path: 'profile', Component: Profile },
        ],
    },
]);
