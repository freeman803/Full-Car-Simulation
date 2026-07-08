function signals = parse_influx(csv_path)

if nargin < 1
    csv_path = 'influx_data.csv';
end

fprintf('Reading %s ...\n', csv_path);

%% ------------------------------------------------------------
% 1. Read CSV
%% ------------------------------------------------------------
fid = fopen(csv_path, 'r');
if fid == -1
    error('Cannot open file: %s', csv_path);
end

skip = 0;
while ~feof(fid)
    line = fgetl(fid);
    if ischar(line) && startsWith(strtrim(line), '#')
        skip = skip + 1;
    else
        break;
    end
end
fclose(fid);

opts = detectImportOptions(csv_path, ...
    'NumHeaderLines', skip, ...
    'Delimiter', ',', ...
    'VariableNamingRule', 'preserve');

T = readtable(csv_path, opts);

col_names = T.Properties.VariableNames;

col_time  = find(strcmp(col_names, '_time'), 1);
col_value = find(strcmp(col_names, '_value'), 1);
col_field = find(strcmp(col_names, '_field'), 1);

%% ------------------------------------------------------------
% 2. Parse timestamps
%% ------------------------------------------------------------
ts_raw = T{:, col_time};

ts_clean = strrep(ts_raw, 'T', ' ');
ts_clean = strrep(ts_clean, 'Z', '');

ts_sec_str = cellfun(@(s) s(1:19), ts_clean, 'UniformOutput', false);

t_sec = datetime(ts_sec_str, ...
    'InputFormat', 'uuuu-MM-dd HH:mm:ss', ...
    'TimeZone', 'UTC');

% fractional seconds
frac_s = zeros(numel(ts_clean), 1);
for i = 1:numel(ts_clean)
    dot_idx = strfind(ts_clean{i}, '.');
    if ~isempty(dot_idx)
        frac_str = ts_clean{i}(dot_idx+1:end);
        frac_s(i) = str2double(['0.' frac_str]);
    end
end

t = t_sec + seconds(frac_s);
t.TimeZone = "UTC";

%% ------------------------------------------------------------
% 3. Extract values
%% ------------------------------------------------------------
values      = T{:, col_value};
field_names = T{:, col_field};

valid = ~cellfun(@isempty, field_names) & ~isnan(values);

t           = t(valid);
values      = values(valid);
field_names = field_names(valid);

%% ------------------------------------------------------------
% 4. Build per-signal structs
%% ------------------------------------------------------------
unique_signals = unique(field_names);

signals = struct();

for s = 1:numel(unique_signals)

    sig = unique_signals{s};
    mask = strcmp(field_names, sig);

    t_sig = t(mask);
    v_sig = values(mask);

    [t_sig, idx] = sort(t_sig);
    v_sig = v_sig(idx);

    entry.name       = sig;
    entry.time_raw   = t_sig;
    entry.value_raw  = v_sig;
    entry.n          = numel(v_sig);

    if numel(t_sig) > 1
        entry.duration_s = seconds(t_sig(end) - t_sig(1));
    else
        entry.duration_s = 0;
    end

    entry.time  = t_sig;
    entry.value = v_sig;

    signals.(matlab.lang.makeValidName(sig)) = entry;

end

%% ------------------------------------------------------------
% 5. SAFE UNION GRID (NO TIMEZONE BUGS)
%% ------------------------------------------------------------
sig_names = fieldnames(signals);

% enforce TZ consistency
for s = 1:numel(sig_names)
    signals.(sig_names{s}).time_raw.TimeZone = "UTC";
end

% build union safely
common_time = signals.(sig_names{1}).time_raw;

for s = 2:numel(sig_names)
    common_time = union(common_time, signals.(sig_names{s}).time_raw);
end

common_time.TimeZone = "UTC";

fprintf('Union grid: %d points (%.2f s)\n', ...
    numel(common_time), seconds(common_time(end) - common_time(1)));

%% ------------------------------------------------------------
% 6. ZOH RESAMPLING (SAFE)
%% ------------------------------------------------------------
t0 = common_time(1);
t_num = seconds(common_time - t0);

for s = 1:numel(sig_names)

    entry = signals.(sig_names{s});

    t_sig = seconds(entry.time_raw - t0);
    v_sig = entry.value_raw;

    v_out = interp1(t_sig, v_sig, t_num, 'previous', NaN);

    entry.time  = common_time;
    entry.value = v_out;

    signals.(sig_names{s}) = entry;

end

signals.time = common_time;

fprintf('Done. signals.time = %d points\n', numel(common_time));

end