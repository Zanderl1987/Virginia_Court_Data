function struttura = mt_sub_t1_ss_cf( struttura, BGinit, RtIns )
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% struttura = mt_sub_t1_ss_cf( struttura, BGinit, RtIns )
% Calculates the steady-state for a given glucose level / insulin path.
% BGinit - glucose concentration in equilibrium
% RtIns - 0 for insulin transport to plasma, 1 for insulin transport to liver.
% Returned structure will contain basal necessary to maintain the desired
% concentration, as well as initial state values for the insulin transport
% chain.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    %% Stead-state calculation

    % Risk will under the assumption that no glucagon secretion takes place 
    % in the desired glucose concentration level.

    if BGinit<struttura.Gb
        fGp=log(BGinit)^struttura.r1-struttura.r2;
        risk=10*fGp^2;
    else
        risk=0;
    end
    if BGinit*struttura.Vg>struttura.ke2
        Et=struttura.ke1*(BGinit*struttura.Vg-struttura.ke2);
    else
        Et=0;
    end

    Gpop=BGinit*struttura.Vg;
    GGta=-struttura.k2-struttura.Vmx*(1+struttura.r3*risk)*struttura.k2/struttura.kp3;
    GGtb=struttura.k1*Gpop-struttura.k2*struttura.Km0-struttura.Vm0+...
       struttura.Vmx*(1+struttura.r3*risk)*struttura.Ib+...
        (struttura.Vmx*(1+struttura.r3*risk)*(struttura.k1+struttura.kp2)*Gpop...
        -struttura.Vmx*(1+struttura.r3*risk)*struttura.kp1...
        +struttura.Vmx*(1+struttura.r3*risk)*(struttura.Fsnc+Et))/struttura.kp3;
    GGtc=struttura.k1*Gpop*struttura.Km0;
    Gtop=(-GGtb-sqrt(GGtb^2-4*GGta*GGtc))/(2*GGta);
%     Idop=max([-1000000 (-(struttura.k1+struttura.kp2)*Gpop+struttura.k2*Gtop+struttura.kp1-(struttura.Fsnc+Et))/struttura.kp3]);
    Idop=max([0 (-(struttura.k1+struttura.kp2)*Gpop+struttura.k2*Gtop+struttura.kp1-(struttura.Fsnc+Et))/struttura.kp3]);
    Ipop=Idop*struttura.Vi;
    Xop=Ipop/struttura.Vi-struttura.Ib;

    %% Insulin infusion rate calculation

    %  Infusion rate necessary to maintain corresponding equilibrium using the
    %  specified insulin path. Useful when configuring external insulin
    %  transport routes.

    if RtIns
        struttura.u2ss   = 0;
        ILop_ip          = (struttura.m2+struttura.m4)*Ipop/struttura.m1;
        struttura.u2ssip = ((struttura.m1+struttura.m30)*ILop_ip - struttura.m2*Ipop);
        ILop             = (struttura.m2 * Ipop+struttura.u2ssip) / (struttura.m1+struttura.m30);
    else
        ILop             = struttura.m2 * Ipop / (struttura.m1+struttura.m30);
        struttura.u2ss   = ((struttura.m2+struttura.m4)*Ipop-struttura.m1*ILop);
        struttura.u2ssip = 0;
    end

    %% Initial state

    struttura.x0=[Gpop Gtop Ipop Xop Idop Idop ILop Gpop struttura.Gnb 0 struttura.k01g/struttura.Vgn*struttura.Gnb];

end