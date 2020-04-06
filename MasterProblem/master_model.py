from gurobipy import *


def run_master_model(parameters):

    try:
        m = Model("Heuristic Master")
        m.setParam('TimeLimit', 60 * 60)

        # ------ SETS -----------------------------------------------------------------------------
        Stations = parameters.stations
        Swap_Stations = Stations  # Har ikke med depot atm
        Vehicles = parameters.vehicles
        Routes = parameters.routes
        Patterns = parameters.patterns
        Scenarios = parameters.scenarios

        # ------ PARAMETERS -----------------------------------------------------------------------
        A = parameters.origin_matrix
        R = parameters.subproblem_objectives
        P = parameters.scenario_probabilities
        Q_FCL = parameters.pattern_fcl
        Q_CCL = parameters.pattern_ccl
        Q_FCU = parameters.pattern_fcu
        Q_CCU = parameters.pattern_ccu
        Q_B = parameters.pattern_b
        Q_CV = parameters.vehicle_bike_caps
        Q_S = parameters.station_caps
        L_FV = parameters.init_flat_bike_load
        L_CV = parameters.init_charged_bike_load
        L_FS = parameters.init_flat_station_load
        L_CS = parameters.init_charged_station_load

        # ------ VARIABLES ------------------------------------------------------------------------
        lam = m.addVars({(v, r, p, s) for v in Vehicles for r in Routes[v] for p in Patterns[v] for s in
                         Scenarios},
                        vtype=GRB.CONTINUOUS, lb=0, ub=1, name="lam")

        x = m.addVars({(i, v, s) for i in Stations for v in Vehicles for s in Scenarios}, vtype=GRB.BINARY,
                      name="x")
        q_FCL = m.addVars({(v, s) for v in Vehicles for s in Scenarios}, vtype=GRB.INTEGER, lb=0, name="q_FCL")
        q_CCL = m.addVars({(v, s) for v in Vehicles for s in Scenarios}, vtype=GRB.INTEGER, lb=0, name="q_CCL")
        q_FCU = m.addVars({(v, s) for v in Vehicles for s in Scenarios}, vtype=GRB.INTEGER, lb=0, name="q_FCU")
        q_CCU = m.addVars({(v, s) for v in Vehicles for s in Scenarios}, vtype=GRB.INTEGER, lb=0, name="q_CCU")
        q_B = m.addVars({(v, s) for v in Vehicles for s in Scenarios}, vtype=GRB.INTEGER, lb=0, name="q_B")

        x_nac = m.addVars({(i,v) for i in Stations for v in Vehicles}, vtype=GRB.CONTINUOUS, lb=0, name="x_nac")
        q_FCL_nac = m.addVars({(v) for v in Vehicles}, vtype=GRB.CONTINUOUS, lb=0,
                              name="q_FCL_nac")
        q_CCL_nac = m.addVars({(v) for v in Vehicles}, vtype=GRB.CONTINUOUS, lb=0,
                             name="q_CCL_nac")
        q_FCU_nac = m.addVars({(v) for v in Vehicles}, vtype=GRB.CONTINUOUS, lb=0,
                             name="q_FCU_nac")
        q_CCU_nac = m.addVars({(v) for v in Vehicles}, vtype=GRB.CONTINUOUS, lb=0,
                             name="q_CCU_nac")
        q_B_nac = m.addVars({(v) for v in Vehicles}, vtype=GRB.CONTINUOUS, lb=0,
                             name="q_B_nac")

        # ------ CONSTRAINTS -----------------------------------------------------------------------
        m.addConstrs(quicksum(A[v][r][i] * lam[(v, r, p, s)] for r in Routes[v] for p in Patterns[v]) == x[(i, v, s)]
                     for i in Swap_Stations for v in Vehicles for s in Scenarios)

        m.addConstrs(x.sum('*', v, s) <= 1 for v in Vehicles for s in Scenarios)
        m.addConstrs(x.sum(i, '*', s) <= 1 for i in Swap_Stations for s in Scenarios)

        m.addConstrs(
            quicksum(lam[(v, r, p, s)] * Q_FCL[v][r][p] for r in Routes[v] for p in Patterns[v]) == q_FCL[
                (v, s)] for v in Vehicles for s in Scenarios)
        m.addConstrs(
            quicksum(lam[(v, r, p, s)] * Q_CCL[v][r][p] for r in Routes[v] for p in Patterns[v]) == q_CCL[
                (v, s)] for v in Vehicles for s in Scenarios)
        m.addConstrs(
            quicksum(lam[(v, r, p, s)] * Q_FCU[v][r][p] for r in Routes[v] for p in Patterns[v]) == q_FCU[
                (v, s)] for v in Vehicles for s in Scenarios)
        m.addConstrs(
            quicksum(lam[(v, r, p, s)] * Q_CCU[v][r][p] for r in Routes[v] for p in Patterns[v]) == q_CCU[
                (v, s)] for v in Vehicles for s in Scenarios)
        m.addConstrs(
            quicksum(lam[(v, r, p, s)] * Q_FCL[v][r][p] for r in Routes[v] for p in Patterns[v]) == q_FCL[
                (v, s)] for v in Vehicles for s in Scenarios)
        m.addConstrs(
            quicksum(lam[(v, r, p, s)] * Q_B[v][r][p] for r in Routes[v] for p in Patterns[v]) == q_B[
                (v, s)] for v in Vehicles for s in Scenarios)

        # Secure that first move is legal in terms of capacities
        m.addConstrs(q_CCL_nac[v] + q_FCL_nac[v] <= Q_CV[v] - L_FV[v] - L_CV[v] + q_CCU_nac[v] + q_FCU_nac[v] for v in
                    Vehicles)
        m.addConstrs(q_CCU_nac[v] + q_FCU_nac[v] <= Q_S[v] - L_CS[v] - L_FS[v] + q_CCL_nac[v] + q_FCL_nac[v] for v in
                    Vehicles)
        m.addConstrs(q_B_nac[v] <= L_FS[v] + q_FCU_nac[v] - q_FCL_nac[v] for v in Vehicles)

        # Non-anticipativity constraints
        m.addConstrs(x_nac[(i, v)] == x[(i, v, s)] for i in Stations for v in Vehicles for s in Scenarios)
        m.addConstrs(q_FCL_nac[v] == q_FCL[(v, s)] for v in Vehicles for s in Scenarios)
        m.addConstrs(q_CCL_nac[v] == q_CCL[(v, s)] for v in Vehicles for s in Scenarios)
        m.addConstrs(q_FCU_nac[v] == q_FCU[(v, s)] for v in Vehicles for s in Scenarios)
        m.addConstrs(q_CCU_nac[v] == q_CCU[(v, s)] for v in Vehicles for s in Scenarios)

        # ------ OBJECTIVE -----------------------------------------------------------------------
        m.setObjective(quicksum(P[s] * R[v][r][p][s] * lam[(v, r, p, s)] for s in Scenarios for v in Vehicles for r in Routes[v] for p in Patterns[v]), GRB.MAXIMIZE)

        m.optimize()

        return m

    except GurobiError:
            print(GurobiError.message)
