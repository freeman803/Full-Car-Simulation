if ~exist('signals', 'var') || isempty(signals)
    signals = parse_influx('');
end
wheelRPM = signals.VCREAR_axleSpeedRear.value;
motorRPM = signals.PM100DX_motorSpeed.value;
wheelOmega = wheelRPM *2*pi/60;
motorTorque = signals.PM100DX_feedbackTorque.value;
axleTorque = motorTorque*4.6;
packVoltage = signals.BMSB_packVoltage.value;
packCurrent = signals.BMSB_packCurrent.value;
packPower = packVoltage .* packCurrent; %watts
mechanicalPower = wheelOmega .* axleTorque; %watts
insteff = mechanicalPower ./ packPower;
eff = sum(mechanicalPower) ./ sum(packPower);
disp('mean eff');
disp((eff));
%% ===== RPM 15–615 =====
mask1  = (motorRPM>=15)  & (motorRPM<615)  & (motorTorque>=2.5)   & (motorTorque<17.5);
mask2  = (motorRPM>=15)  & (motorRPM<615)  & (motorTorque>=17.5)  & (motorTorque<32.5);
mask3  = (motorRPM>=15)  & (motorRPM<615)  & (motorTorque>=32.5)  & (motorTorque<47.5);
mask4  = (motorRPM>=15)  & (motorRPM<615)  & (motorTorque>=47.5)  & (motorTorque<62.5);
mask5  = (motorRPM>=15)  & (motorRPM<615)  & (motorTorque>=62.5)  & (motorTorque<77.5);
mask6  = (motorRPM>=15)  & (motorRPM<615)  & (motorTorque>=77.5)  & (motorTorque<92.5);
mask7  = (motorRPM>=15)  & (motorRPM<615)  & (motorTorque>=92.5)  & (motorTorque<107.5);
mask8  = (motorRPM>=15)  & (motorRPM<615)  & (motorTorque>=107.5) & (motorTorque<122.5);
mask9  = (motorRPM>=15)  & (motorRPM<615)  & (motorTorque>=122.5) & (motorTorque<137.5);
mask10 = (motorRPM>=15)  & (motorRPM<615)  & (motorTorque>=137.5) & (motorTorque<152.5);
effGroup1  = mean(insteff(mask1));
effGroup2  = mean(insteff(mask2));
effGroup3  = mean(insteff(mask3));
effGroup4  = mean(insteff(mask4));
effGroup5  = mean(insteff(mask5));
effGroup6  = mean(insteff(mask6));
effGroup7  = mean(insteff(mask7));
effGroup8  = mean(insteff(mask8));
effGroup9  = mean(insteff(mask9));
effGroup10 = mean(insteff(mask10));

%% ===== RPM 615–1215 =====
mask11 = (motorRPM>=615)  & (motorRPM<1215) & (motorTorque>=2.5)   & (motorTorque<17.5);
mask12 = (motorRPM>=615)  & (motorRPM<1215) & (motorTorque>=17.5)  & (motorTorque<32.5);
mask13 = (motorRPM>=615)  & (motorRPM<1215) & (motorTorque>=32.5)  & (motorTorque<47.5);
mask14 = (motorRPM>=615)  & (motorRPM<1215) & (motorTorque>=47.5)  & (motorTorque<62.5);
mask15 = (motorRPM>=615)  & (motorRPM<1215) & (motorTorque>=62.5)  & (motorTorque<77.5);
mask16 = (motorRPM>=615)  & (motorRPM<1215) & (motorTorque>=77.5)  & (motorTorque<92.5);
mask17 = (motorRPM>=615)  & (motorRPM<1215) & (motorTorque>=92.5)  & (motorTorque<107.5);
mask18 = (motorRPM>=615)  & (motorRPM<1215) & (motorTorque>=107.5) & (motorTorque<122.5);
mask19 = (motorRPM>=615)  & (motorRPM<1215) & (motorTorque>=122.5) & (motorTorque<137.5);
mask20 = (motorRPM>=615)  & (motorRPM<1215) & (motorTorque>=137.5) & (motorTorque<152.5);
effGroup11 = mean(insteff(mask11));
effGroup12 = mean(insteff(mask12));
effGroup13 = mean(insteff(mask13));
effGroup14 = mean(insteff(mask14));
effGroup15 = mean(insteff(mask15));
effGroup16 = mean(insteff(mask16));
effGroup17 = mean(insteff(mask17));
effGroup18 = mean(insteff(mask18));
effGroup19 = mean(insteff(mask19));
effGroup20 = mean(insteff(mask20));

%% ===== RPM 1215–1815 =====
mask21 = (motorRPM>=1215) & (motorRPM<1815) & (motorTorque>=2.5)   & (motorTorque<17.5);
mask22 = (motorRPM>=1215) & (motorRPM<1815) & (motorTorque>=17.5)  & (motorTorque<32.5);
mask23 = (motorRPM>=1215) & (motorRPM<1815) & (motorTorque>=32.5)  & (motorTorque<47.5);
mask24 = (motorRPM>=1215) & (motorRPM<1815) & (motorTorque>=47.5)  & (motorTorque<62.5);
mask25 = (motorRPM>=1215) & (motorRPM<1815) & (motorTorque>=62.5)  & (motorTorque<77.5);
mask26 = (motorRPM>=1215) & (motorRPM<1815) & (motorTorque>=77.5)  & (motorTorque<92.5);
mask27 = (motorRPM>=1215) & (motorRPM<1815) & (motorTorque>=92.5)  & (motorTorque<107.5);
mask28 = (motorRPM>=1215) & (motorRPM<1815) & (motorTorque>=107.5) & (motorTorque<122.5);
mask29 = (motorRPM>=1215) & (motorRPM<1815) & (motorTorque>=122.5) & (motorTorque<137.5);
mask30 = (motorRPM>=1215) & (motorRPM<1815) & (motorTorque>=137.5) & (motorTorque<152.5);
effGroup21 = mean(insteff(mask21));
effGroup22 = mean(insteff(mask22));
effGroup23 = mean(insteff(mask23));
effGroup24 = mean(insteff(mask24));
effGroup25 = mean(insteff(mask25));
effGroup26 = mean(insteff(mask26));
effGroup27 = mean(insteff(mask27));
effGroup28 = mean(insteff(mask28));
effGroup29 = mean(insteff(mask29));
effGroup30 = mean(insteff(mask30));

%% ===== RPM 1815–2415 =====
mask31 = (motorRPM>=1815) & (motorRPM<2415) & (motorTorque>=2.5)   & (motorTorque<17.5);
mask32 = (motorRPM>=1815) & (motorRPM<2415) & (motorTorque>=17.5)  & (motorTorque<32.5);
mask33 = (motorRPM>=1815) & (motorRPM<2415) & (motorTorque>=32.5)  & (motorTorque<47.5);
mask34 = (motorRPM>=1815) & (motorRPM<2415) & (motorTorque>=47.5)  & (motorTorque<62.5);
mask35 = (motorRPM>=1815) & (motorRPM<2415) & (motorTorque>=62.5)  & (motorTorque<77.5);
mask36 = (motorRPM>=1815) & (motorRPM<2415) & (motorTorque>=77.5)  & (motorTorque<92.5);
mask37 = (motorRPM>=1815) & (motorRPM<2415) & (motorTorque>=92.5)  & (motorTorque<107.5);
mask38 = (motorRPM>=1815) & (motorRPM<2415) & (motorTorque>=107.5) & (motorTorque<122.5);
mask39 = (motorRPM>=1815) & (motorRPM<2415) & (motorTorque>=122.5) & (motorTorque<137.5);
mask40 = (motorRPM>=1815) & (motorRPM<2415) & (motorTorque>=137.5) & (motorTorque<152.5);
effGroup31 = mean(insteff(mask31));
effGroup32 = mean(insteff(mask32));
effGroup33 = mean(insteff(mask33));
effGroup34 = mean(insteff(mask34));
effGroup35 = mean(insteff(mask35));
effGroup36 = mean(insteff(mask36));
effGroup37 = mean(insteff(mask37));
effGroup38 = mean(insteff(mask38));
effGroup39 = mean(insteff(mask39));
effGroup40 = mean(insteff(mask40));

%% ===== RPM 2415–3015 =====
mask41 = (motorRPM>=2415) & (motorRPM<3015) & (motorTorque>=2.5)   & (motorTorque<17.5);
mask42 = (motorRPM>=2415) & (motorRPM<3015) & (motorTorque>=17.5)  & (motorTorque<32.5);
mask43 = (motorRPM>=2415) & (motorRPM<3015) & (motorTorque>=32.5)  & (motorTorque<47.5);
mask44 = (motorRPM>=2415) & (motorRPM<3015) & (motorTorque>=47.5)  & (motorTorque<62.5);
mask45 = (motorRPM>=2415) & (motorRPM<3015) & (motorTorque>=62.5)  & (motorTorque<77.5);
mask46 = (motorRPM>=2415) & (motorRPM<3015) & (motorTorque>=77.5)  & (motorTorque<92.5);
mask47 = (motorRPM>=2415) & (motorRPM<3015) & (motorTorque>=92.5)  & (motorTorque<107.5);
mask48 = (motorRPM>=2415) & (motorRPM<3015) & (motorTorque>=107.5) & (motorTorque<122.5);
mask49 = (motorRPM>=2415) & (motorRPM<3015) & (motorTorque>=122.5) & (motorTorque<137.5);
mask50 = (motorRPM>=2415) & (motorRPM<3015) & (motorTorque>=137.5) & (motorTorque<152.5);
effGroup41 = mean(insteff(mask41));
effGroup42 = mean(insteff(mask42));
effGroup43 = mean(insteff(mask43));
effGroup44 = mean(insteff(mask44));
effGroup45 = mean(insteff(mask45));
effGroup46 = mean(insteff(mask46));
effGroup47 = mean(insteff(mask47));
effGroup48 = mean(insteff(mask48));
effGroup49 = mean(insteff(mask49));
effGroup50 = mean(insteff(mask50));

%% ===== RPM 3015–3615 =====
mask51 = (motorRPM>=3015) & (motorRPM<3615) & (motorTorque>=2.5)   & (motorTorque<17.5);
mask52 = (motorRPM>=3015) & (motorRPM<3615) & (motorTorque>=17.5)  & (motorTorque<32.5);
mask53 = (motorRPM>=3015) & (motorRPM<3615) & (motorTorque>=32.5)  & (motorTorque<47.5);
mask54 = (motorRPM>=3015) & (motorRPM<3615) & (motorTorque>=47.5)  & (motorTorque<62.5);
mask55 = (motorRPM>=3015) & (motorRPM<3615) & (motorTorque>=62.5)  & (motorTorque<77.5);
mask56 = (motorRPM>=3015) & (motorRPM<3615) & (motorTorque>=77.5)  & (motorTorque<92.5);
mask57 = (motorRPM>=3015) & (motorRPM<3615) & (motorTorque>=92.5)  & (motorTorque<107.5);
mask58 = (motorRPM>=3015) & (motorRPM<3615) & (motorTorque>=107.5) & (motorTorque<122.5);
mask59 = (motorRPM>=3015) & (motorRPM<3615) & (motorTorque>=122.5) & (motorTorque<137.5);
mask60 = (motorRPM>=3015) & (motorRPM<3615) & (motorTorque>=137.5) & (motorTorque<152.5);
effGroup51 = mean(insteff(mask51));
effGroup52 = mean(insteff(mask52));
effGroup53 = mean(insteff(mask53));
effGroup54 = mean(insteff(mask54));
effGroup55 = mean(insteff(mask55));
effGroup56 = mean(insteff(mask56));
effGroup57 = mean(insteff(mask57));
effGroup58 = mean(insteff(mask58));
effGroup59 = mean(insteff(mask59));
effGroup60 = mean(insteff(mask60));

%% ===== RPM 3615–4215 =====
mask61 = (motorRPM>=3615) & (motorRPM<4215) & (motorTorque>=2.5)   & (motorTorque<17.5);
mask62 = (motorRPM>=3615) & (motorRPM<4215) & (motorTorque>=17.5)  & (motorTorque<32.5);
mask63 = (motorRPM>=3615) & (motorRPM<4215) & (motorTorque>=32.5)  & (motorTorque<47.5);
mask64 = (motorRPM>=3615) & (motorRPM<4215) & (motorTorque>=47.5)  & (motorTorque<62.5);
mask65 = (motorRPM>=3615) & (motorRPM<4215) & (motorTorque>=62.5)  & (motorTorque<77.5);
mask66 = (motorRPM>=3615) & (motorRPM<4215) & (motorTorque>=77.5)  & (motorTorque<92.5);
mask67 = (motorRPM>=3615) & (motorRPM<4215) & (motorTorque>=92.5)  & (motorTorque<107.5);
mask68 = (motorRPM>=3615) & (motorRPM<4215) & (motorTorque>=107.5) & (motorTorque<122.5);
mask69 = (motorRPM>=3615) & (motorRPM<4215) & (motorTorque>=122.5) & (motorTorque<137.5);
mask70 = (motorRPM>=3615) & (motorRPM<4215) & (motorTorque>=137.5) & (motorTorque<152.5);
effGroup61 = mean(insteff(mask61));
effGroup62 = mean(insteff(mask62));
effGroup63 = mean(insteff(mask63));
effGroup64 = mean(insteff(mask64));
effGroup65 = mean(insteff(mask65));
effGroup66 = mean(insteff(mask66));
effGroup67 = mean(insteff(mask67));
effGroup68 = mean(insteff(mask68));
effGroup69 = mean(insteff(mask69));
effGroup70 = mean(insteff(mask70));

%% ===== RPM 4215–4815 =====
mask71 = (motorRPM>=4215) & (motorRPM<4815) & (motorTorque>=2.5)   & (motorTorque<17.5);
mask72 = (motorRPM>=4215) & (motorRPM<4815) & (motorTorque>=17.5)  & (motorTorque<32.5);
mask73 = (motorRPM>=4215) & (motorRPM<4815) & (motorTorque>=32.5)  & (motorTorque<47.5);
mask74 = (motorRPM>=4215) & (motorRPM<4815) & (motorTorque>=47.5)  & (motorTorque<62.5);
mask75 = (motorRPM>=4215) & (motorRPM<4815) & (motorTorque>=62.5)  & (motorTorque<77.5);
mask76 = (motorRPM>=4215) & (motorRPM<4815) & (motorTorque>=77.5)  & (motorTorque<92.5);
mask77 = (motorRPM>=4215) & (motorRPM<4815) & (motorTorque>=92.5)  & (motorTorque<107.5);
mask78 = (motorRPM>=4215) & (motorRPM<4815) & (motorTorque>=107.5) & (motorTorque<122.5);
mask79 = (motorRPM>=4215) & (motorRPM<4815) & (motorTorque>=122.5) & (motorTorque<137.5);
mask80 = (motorRPM>=4215) & (motorRPM<4815) & (motorTorque>=137.5) & (motorTorque<152.5);
effGroup71 = mean(insteff(mask71));
effGroup72 = mean(insteff(mask72));
effGroup73 = mean(insteff(mask73));
effGroup74 = mean(insteff(mask74));
effGroup75 = mean(insteff(mask75));
effGroup76 = mean(insteff(mask76));
effGroup77 = mean(insteff(mask77));
effGroup78 = mean(insteff(mask78));
effGroup79 = mean(insteff(mask79));
effGroup80 = mean(insteff(mask80));

%% ===== RPM 4815–5415 =====
mask81 = (motorRPM>=4815) & (motorRPM<5415) & (motorTorque>=2.5)   & (motorTorque<17.5);
mask82 = (motorRPM>=4815) & (motorRPM<5415) & (motorTorque>=17.5)  & (motorTorque<32.5);
mask83 = (motorRPM>=4815) & (motorRPM<5415) & (motorTorque>=32.5)  & (motorTorque<47.5);
mask84 = (motorRPM>=4815) & (motorRPM<5415) & (motorTorque>=47.5)  & (motorTorque<62.5);
mask85 = (motorRPM>=4815) & (motorRPM<5415) & (motorTorque>=62.5)  & (motorTorque<77.5);
mask86 = (motorRPM>=4815) & (motorRPM<5415) & (motorTorque>=77.5)  & (motorTorque<92.5);
mask87 = (motorRPM>=4815) & (motorRPM<5415) & (motorTorque>=92.5)  & (motorTorque<107.5);
mask88 = (motorRPM>=4815) & (motorRPM<5415) & (motorTorque>=107.5) & (motorTorque<122.5);
mask89 = (motorRPM>=4815) & (motorRPM<5415) & (motorTorque>=122.5) & (motorTorque<137.5);
mask90 = (motorRPM>=4815) & (motorRPM<5415) & (motorTorque>=137.5) & (motorTorque<152.5);
effGroup81 = mean(insteff(mask81));
effGroup82 = mean(insteff(mask82));
effGroup83 = mean(insteff(mask83));
effGroup84 = mean(insteff(mask84));
effGroup85 = mean(insteff(mask85));
effGroup86 = mean(insteff(mask86));
effGroup87 = mean(insteff(mask87));
effGroup88 = mean(insteff(mask88));
effGroup89 = mean(insteff(mask89));
effGroup90 = mean(insteff(mask90));

%% ===== RPM 5415–6015 =====
mask91  = (motorRPM>=5415) & (motorRPM<6015) & (motorTorque>=2.5)   & (motorTorque<17.5);
mask92  = (motorRPM>=5415) & (motorRPM<6015) & (motorTorque>=17.5)  & (motorTorque<32.5);
mask93  = (motorRPM>=5415) & (motorRPM<6015) & (motorTorque>=32.5)  & (motorTorque<47.5);
mask94  = (motorRPM>=5415) & (motorRPM<6015) & (motorTorque>=47.5)  & (motorTorque<62.5);
mask95  = (motorRPM>=5415) & (motorRPM<6015) & (motorTorque>=62.5)  & (motorTorque<77.5);
mask96  = (motorRPM>=5415) & (motorRPM<6015) & (motorTorque>=77.5)  & (motorTorque<92.5);
mask97  = (motorRPM>=5415) & (motorRPM<6015) & (motorTorque>=92.5)  & (motorTorque<107.5);
mask98  = (motorRPM>=5415) & (motorRPM<6015) & (motorTorque>=107.5) & (motorTorque<122.5);
mask99  = (motorRPM>=5415) & (motorRPM<6015) & (motorTorque>=122.5) & (motorTorque<137.5);
mask100 = (motorRPM>=5415) & (motorRPM<6015) & (motorTorque>=137.5) & (motorTorque<152.5);
effGroup91  = mean(insteff(mask91));
effGroup92  = mean(insteff(mask92));
effGroup93  = mean(insteff(mask93));
effGroup94  = mean(insteff(mask94));
effGroup95  = mean(insteff(mask95));
effGroup96  = mean(insteff(mask96));
effGroup97  = mean(insteff(mask97));
effGroup98  = mean(insteff(mask98));
effGroup99  = mean(insteff(mask99));
effGroup100 = mean(insteff(mask100));

%% ===== 3D efficiency map =====
torqueCenters = 10:15:145;       % 10 torque-bin centers (Nm): 2.5–17.5 -> 10, ...
speedCenters  = 315:600:5715;    % 10 speed-band centers (RPM): 15–615 -> 315, ...

effVec = [effGroup1   effGroup2   effGroup3   effGroup4   effGroup5   effGroup6   effGroup7   effGroup8   effGroup9   effGroup10 ...
          effGroup11  effGroup12  effGroup13  effGroup14  effGroup15  effGroup16  effGroup17  effGroup18  effGroup19  effGroup20 ...
          effGroup21  effGroup22  effGroup23  effGroup24  effGroup25  effGroup26  effGroup27  effGroup28  effGroup29  effGroup30 ...
          effGroup31  effGroup32  effGroup33  effGroup34  effGroup35  effGroup36  effGroup37  effGroup38  effGroup39  effGroup40 ...
          effGroup41  effGroup42  effGroup43  effGroup44  effGroup45  effGroup46  effGroup47  effGroup48  effGroup49  effGroup50 ...
          effGroup51  effGroup52  effGroup53  effGroup54  effGroup55  effGroup56  effGroup57  effGroup58  effGroup59  effGroup60 ...
          effGroup61  effGroup62  effGroup63  effGroup64  effGroup65  effGroup66  effGroup67  effGroup68  effGroup69  effGroup70 ...
          effGroup71  effGroup72  effGroup73  effGroup74  effGroup75  effGroup76  effGroup77  effGroup78  effGroup79  effGroup80 ...
          effGroup81  effGroup82  effGroup83  effGroup84  effGroup85  effGroup86  effGroup87  effGroup88  effGroup89  effGroup90 ...
          effGroup91  effGroup92  effGroup93  effGroup94  effGroup95  effGroup96  effGroup97  effGroup98  effGroup99  effGroup100];
effMat = reshape(effVec, 10, 10);   % rows = torque bin, cols = speed band

Z = effMat.';                       % rows = speed, cols = torque
figure;
surf(torqueCenters, speedCenters, Z);
xlabel('Motor torque (Nm)');
ylabel('Motor speed (RPM)');
zlabel('Efficiency');
title('Drivetrain efficiency map');
colorbar; shading interp; view(135, 30);
zlim([0 1]);