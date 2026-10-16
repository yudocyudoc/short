within;
package IGCS2MakeToOrder
  "S2: independently defined synthetic queue; stocks and restricted flows use BSD SystemDynamics"
  partial model Scenario
    parameter Real capacityPreparing=10 "Maximum preparation throughput, orders/hour";
    parameter Real capacityDispatch=8 "Maximum dispatch throughput, orders/hour";
    parameter Real preparationResponseTime=0.5 "Work-response time, hours";
    parameter Real dispatchResponseTime=0.5 "Finished-stock response time, hours";
    parameter Real tRush=2 "Start of surge, hours";
    parameter Real tStop=4 "Stop accepting new orders, hours";
    parameter Real beforeRush=6 "Accepted orders/hour";
    parameter Real duringRush=16 "Accepted orders/hour";
    Real acceptedRate "Exogenously accepted orders/hour";
    Real preparationRate "Work converted into prepared orders/hour";
    Real dispatchRate "Prepared orders delivered/hour";
    Real unpreparedOrders "Accepted but not yet prepared";
    Real preparedOrders "Prepared but not yet delivered";
    Real deliveredOrders "Cumulative deliveries";
  equation
    acceptedRate = if time < tRush then beforeRush else if time < tStop then duringRush else 0;
  end Scenario;

  model Equations
    "Counterfactual reference: explicitly written conservation and rate bounds"
    extends Scenario;
  initial equation
    unpreparedOrders = 0;
    preparedOrders = 0;
    deliveredOrders = 0;
  equation
    preparationRate = min(capacityPreparing,max(0,unpreparedOrders/preparationResponseTime));
    dispatchRate = min(capacityDispatch,max(0,preparedOrders/dispatchResponseTime));
    der(unpreparedOrders) = acceptedRate - preparationRate;
    der(preparedOrders) = preparationRate - dispatchRate;
    der(deliveredOrders) = dispatchRate;
  end Equations;

  model Components
    "Reusable preexisting library blocks; no custom Modelica differential equations"
    extends Scenario;
    SystemDynamics.Levels.Level awaitingWork(x0=0);
    SystemDynamics.Levels.Level awaitingDispatch(x0=0);
    SystemDynamics.Levels.Level1a deliveredLevel(x0=0);
    SystemDynamics.Rates.Rate_1 accepted;
    SystemDynamics.Rates.RRate prepare(minFlow=0,maxFlow=capacityPreparing);
    SystemDynamics.Rates.RRate dispatch(minFlow=0,maxFlow=capacityDispatch);
  equation
    accepted.u = acceptedRate;
    prepare.u = max(0,awaitingWork.level/preparationResponseTime);
    dispatch.u = max(0,awaitingDispatch.level/dispatchResponseTime);
    connect(accepted.y,awaitingWork.u1);
    connect(prepare.y1,awaitingWork.u2);
    connect(prepare.y,awaitingDispatch.u1);
    connect(dispatch.y1,awaitingDispatch.u2);
    connect(dispatch.y,deliveredLevel.u1);
    unpreparedOrders = awaitingWork.level;
    preparedOrders = awaitingDispatch.level;
    deliveredOrders = deliveredLevel.level;
    preparationRate = prepare.rate;
    dispatchRate = dispatch.rate;
  end Components;
  annotation(uses(Modelica(version="4.0.0"),SystemDynamics(version="2.1.2")));
end IGCS2MakeToOrder;
