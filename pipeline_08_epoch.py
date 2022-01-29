import sys
import json
import mne
import os.path as op
import numpy as np
from utilities import files

# parsing command line arguments
try:
    index = int(sys.argv[1])
except:
    print("incorrect arguments")
    sys.exit()

try:
    json_file = sys.argv[2]
    print("USING:", json_file)
except:
    json_file = "settings.json"
    print("USING:", json_file)

# opening a json file
with open(json_file) as pipeline_file:
    parameters = json.load(pipeline_file)

path = parameters["dataset_path"]
sfreq = parameters["downsample_dataset"]
hi_pass = parameters["hi_pass_filter"]
sub_path = op.join(path, "raw")

der_path = op.join(path, "derivatives")
files.make_folder(der_path)
proc_path = op.join(der_path, "processed")
files.make_folder(proc_path)

subjects = files.get_folders_files(proc_path)[0]
subjects.sort()
subject = subjects[index]
subject_id = subject.split("/")[-1]

print("ID:", subject_id)

sub_path = op.join(proc_path, subject_id)
files.make_folder(sub_path)

sessions = files.get_folders(subject,'ses','')[2]
sessions.sort()

for session in sessions:
    session_id = session.split("/")[-1]

    sess_path = op.join(sub_path, session_id)
    files.make_folder(sess_path)

    qc_folder = op.join(sess_path, "QC")
    files.make_folder(qc_folder)

    raw_paths = files.get_files(sess_path, "zapline-" + subject_id + "-" + session_id, "-raw.fif")[2]
    raw_paths.sort()

    ica_json_file = op.join(
        sess_path,
        "{}-{}-ICA_to_reject.json".format(subject_id, session_id)
    )

    with open(ica_json_file) as ica_file:
        ica_files = json.load(ica_file)

    ica_keys = list(ica_files.keys())
    ica_keys.sort()

    event_paths = files.get_files(sess_path, subject_id+"-"+session_id, "-eve.fif")[2]
    event_paths.sort()

    raw_ica_eve = list(zip(raw_paths, ica_keys, event_paths))

    for (raw_path, ica_key, eve_path) in raw_ica_eve:
        # for (raw_path, ica_key, eve_path) in [raw_ica_eve[3]]:
        ica_path = op.join(
            sess_path,
            ica_key
        )
        numero = str(raw_path.split("-")[-2]).zfill(3)

        print("INPUT RAW FILE:", raw_path)
        print("INPUT EVENT FILE:", eve_path)
        print("INPUT ICA FILE:", ica_path)

        ica_exc = ica_files[ica_key]

        events = mne.read_events(eve_path)

        ica = mne.preprocessing.read_ica(
            ica_path,
            verbose=False
        )

        raw = mne.io.read_raw_fif(
            raw_path,
            verbose=False,
            preload=True
        )

        raw = ica.apply(
            raw,
            exclude=ica_exc,
            verbose=False
        )

        raw.filter(
            l_freq=None,
            h_freq=hi_pass
        )

        epochs_dict = {
            "visual1": [30, -.2, .8, -.2, 0],
            "visual2": [50, -.2, .8, -.2, 0],
            "motor": [60, -.5, .5, -.5, -.3]
        }

        for i in epochs_dict.keys():
            trig, tmin, tmax, bmin, bmax = epochs_dict[i]
            epoch = mne.Epochs(
                raw,
                mne.pick_events(events, include=trig),
                tmin=tmin,
                tmax=tmax,
                baseline=(bmin, bmax),
                verbose=True,
                detrend=1
            )
            # # plotting the psd of the epochs
            # picks = [i for i in raw.ch_names if "O" in i] + [i for i in raw.ch_names if "T" in i]

            # fig = epoch.plot_psd(
            #     show=False,
            #     average=False,
            #     picks=picks
            # )
            # fig.suptitle("{} {}".format(i, numero))
            # f_p = op.join(
            #     qc_folder, "{}-{}-epochs-{}.png".format(subject_id, numero, i)
            # )
            # print(f_p)
            # plt.savefig(
            #     f_p,
            #     dpi=150,
            #     bbox_inches="tight"
            # )
            # plt.close("all")

            epoch_path = op.join(
                sess_path,
                "{}-{}-{}-{}-epo.fif".format(subject_id, session_id, numero, i)
            )

            epoch.save(
                epoch_path,
                fmt="double",
                overwrite=True,
                verbose=False,

            )
            print("SAVED:", epoch_path)

