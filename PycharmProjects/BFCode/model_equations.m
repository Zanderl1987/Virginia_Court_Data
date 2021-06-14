function output = model_equations(x,struttura,U)
    
    It   = U(1);
    In   = U(2);
    Rat  = U(3);
    dxdt = zeros(9,1);
         
    %%
    
    % Hepatic Glucose Production
    EGPt = struttura.kp1-struttura.kp2*max(x(1),0)-struttura.kp3*max(x(5),0)+struttura.kcounter*x(8);

    % Insulin Independent Glucose Utilization
    Uiit = struttura.Fsnc;

    % Renal excretion
    if x(1)>struttura.ke2
        Et = struttura.ke1*(x(1)-struttura.ke2);
    else
        Et = 0;
    end

    % Glucose kinetics
    dxdt(1) = max(EGPt,0)+Rat-Uiit-Et-struttura.k1*max(x(1),0)+struttura.k2*max(x(2),0);

    % Utilization by insulin dependent tissues
    if (x(1)/struttura.Vg>=struttura.Gb)
        risk = 0;
    else % Increased uptake in hypoglycemia
        threshold = 60;
        if (x(1)/struttura.Vg>threshold)

            fGp  = log(x(1)/struttura.Vg)^struttura.r1-struttura.r2;
            risk = 10*fGp^2;

        else

            fGp  = log(threshold)^struttura.r1-struttura.r2;
            risk = 10*fGp^2;

        end
    end

    Vmt = struttura.Vm0 + struttura.Vmx * x(3) * (1+struttura.r3*risk);

    Kmt  = struttura.Km0;
    Uidt = (Vmt*x(2)/(Kmt+x(2)));
    dxdt(2) = -max(Uidt,0)+struttura.k1*max(x(1),0)-struttura.k2*max(x(2),0);  
    
    % Insulin action on glucose utilization
    dxdt(3) = -struttura.p2u*x(3)+struttura.p2u*(In-struttura.Ib);

    % Insulin action on production
    dxdt(4) = -struttura.ki*(x(4)-In);
    dxdt(5) = -struttura.ki*(x(5)-x(4));

    % Subcutaneous glucose
    dxdt(6) = -struttura.ksc*(x(6)-x(1));

    % Glucagon secretion & kinetics
    % Secretion
    Gp = x(1)/struttura.Vg;

    GSRb = struttura.k01g/struttura.Vgn*struttura.Gnb;

    if Gp - struttura.Gth >0
        GSRs = max(struttura.kGSRs2*(struttura.Gth-Gp)+GSRb,0);
    else
        GSRs = max(struttura.kGSRs*(struttura.Gth-Gp)/(max(It-struttura.Ith,0)+1)+GSRb,0);
    end

    dxdt(9) = -struttura.alfaG*(x(9)-GSRs);%

    GSRd = max(-struttura.kGSRd*dxdt(1)/struttura.Vg,0);
    GSR  = GSRd+max(x(9),0);

    % Kinetics
    dxdt(7) = -struttura.k01g/struttura.Vgn*x(7) + GSR;

    % Glucagon action
    dxdt(8) = -struttura.kXGn*x(8)+struttura.kXGn*max(x(7)-struttura.Gnb,0);
    
    %%
    output = dxdt;
    
end