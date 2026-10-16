within;
package IGCS1Parity
  "S1: independently authored mathematical restatement of two Hines mechanisms; no original .mdl bytes."
  constant Real capX[9]={0,0.164706,0.357647,0.578824,0.785882,1,1.20941,1.4,1.5};
  constant Real capY[9]={0,0.234875,0.491103,0.711744,0.86121,1,1.09609,1.15,1.15};
  constant Real shipX[10]={0,0.5,0.621176,0.72,0.818824,0.921176,1,1.11176,1.2,1.5};
  constant Real shipY[10]={0,0.5,0.604982,0.683274,0.768683,0.846975,0.911032,0.975089,1,1};

  function lookup
    input Real ratio;
    input Real xs[:];
    input Real ys[size(xs, 1)];
    output Real y;
  algorithm
    y := ys[1];
    if ratio <= xs[1] then
      y := ys[1];
    elseif ratio >= xs[size(xs,1)] then
      y := ys[size(xs,1)];
    else
      for i in 1:size(xs,1)-1 loop
        if ratio >= xs[i] and ratio <= xs[i+1] then
          y := ys[i] + (ratio-xs[i])*(ys[i+1]-ys[i])/(xs[i+1]-xs[i]);
        end if;
      end for;
    end if;
  end lookup;

  partial model S1Core
    "Constant hypothetical exogenous signals from the existing make-to-stock S1 fixture"
    parameter Real capacity=12 "Hypothetical units per hour";
    parameter Real plannedProduction=8 "Exogenous desired production units per hour";
    parameter Real acceptedOrders=6 "Exogenous accepted orders per hour";
    parameter Real backlog0=5 "Initial accepted but not shipped units";
    parameter Real inventory0=12 "Initial finished goods";
    parameter Real minimumShipTime=0.25 "Hour";
    parameter Real processShipTime=0.5 "Hour";
    Real backlog "Orders pending shipping, NOT work unprepared";
    Real inventory "Finished goods stock";
    Real production "Simulated production rate";
    Real shipping "Simulated shipping rate";
    Real maximumShipping;
    Real indicatedFraction;
    Real fractionOfMaxShipping;
  equation
    production = capacity*lookup(plannedProduction/capacity,capX,capY);
    maximumShipping = inventory/minimumShipTime;
    indicatedFraction = if maximumShipping <> 0 then (backlog/processShipTime)/maximumShipping else 10;
    fractionOfMaxShipping = lookup(indicatedFraction,shipX,shipY);
    shipping = maximumShipping*fractionOfMaxShipping;
  end S1Core;

  model Equations
    "OpenModelica independent stock-flow ODE representation; SAME Hines curve coordinates"
    extends S1Core;
  initial equation
    backlog = backlog0;
    inventory = inventory0;
  equation
    der(backlog) = acceptedOrders-shipping;
    der(inventory) = production-shipping;
  end Equations;

  model Components
    "Same mechanisms, using BSD-licensed SystemDynamics Levels and Rates library"
    extends S1Core;
    SystemDynamics.Levels.Level backlogLevel(x0=backlog0);
    SystemDynamics.Levels.Level inventoryLevel(x0=inventory0);
    SystemDynamics.Rates.Rate_1 arrivalsRate;
    SystemDynamics.Rates.Rate_1 productionRate;
    SystemDynamics.Rates.Rate_1 shippingRate;
  equation
    arrivalsRate.u = acceptedOrders;
    productionRate.u = production;
    shippingRate.u = shipping;
    connect(arrivalsRate.y,backlogLevel.u1);
    connect(shippingRate.y,backlogLevel.u2);
    connect(productionRate.y,inventoryLevel.u1);
    connect(shippingRate.y1,inventoryLevel.u2);
    backlog = backlogLevel.level;
    inventory = inventoryLevel.level;
  end Components;

  annotation(uses(Modelica(version="4.0.0"),SystemDynamics(version="2.1.2")));
end IGCS1Parity;
