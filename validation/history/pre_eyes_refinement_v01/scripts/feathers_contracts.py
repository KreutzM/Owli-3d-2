"""Code-owned #6 evidence inventories and immutable predecessor Git/LFS anchors.

Inventories describe the required proof, never a supplied map's current contents.
The predecessor is the accepted #37 merge. All historical artifacts remain exact.
"""
from review_fixes_contracts import PROTECTED_SHA256 as PREVIOUS_PROTECTED_SHA256
from review_fixes_review import SOURCES as PREVIOUS_SOURCES
from evidence_contracts import DELIVERY_INVENTORIES

BASELINE_COMMIT = '966b7f02489ebad4890ba17a6c64f4c03adc2803'
BASELINE_SCENE = 'blender/scene/owli_review_fixes_v01.blend'
BASELINE_SHA256 = '8685fc054428ec848f20a922c995487f9ac4a2797cbe3713eaeb5e364b02e8fb'
BASELINE_SIZE_BYTES = 1068211
SCENE_PATH = 'blender/scene/owli_feathers_v01.blend'
REVIEW_PATH = 'validation/reviews/feathers_v01'
VIEWS = ('VAL_FRONT', 'VAL_LEFT', 'VAL_BACK', 'VAL_3Q')
RELOAD_FIELDS = ('geometry_sha256', 'new_meshes', 'bindings', 'symmetry',
                 'root_contacts', 'leaf_roots', 'feet', 'studio', 'framing', 'counts', 'movement')
CENTRAL_LAYER_IDS = ('HeadCenter', 'BodyCenter', 'ChestCenter')
REMOVED_MESHES = ('BLK_Wing_L', 'BLK_Wing_R', 'BLK_Tail', 'BLK_Chest',
                  'BLK_ChestAccent_L', 'BLK_ChestAccent_R')
MODES = ('build', 'saved_build', 'reload_a', 'reload_b')
LABELS = ('baseline', 'live_neutral', 'blink', 'beak_open', 'gesture_left',
          'gesture_right', 'gesture_both', 'neutral', 'reload_a', 'reload_b')
EVIDENCE_NAMES = tuple(sorted(
    {f'evidence/{label}/{view}.png' for label in LABELS for view in VIEWS}
    | {view+'.png' for view in VIEWS}
    | {view+'_comparison.png' for view in VIEWS}
    | {'contact_sheet.png'}
    | {mode+'_checks.json' for mode in MODES}
    | {mode+'.log' for mode in MODES}))
MANUAL_EVIDENCE_NAMES = tuple(sorted(
    {'verification.json', 'report.md', 'independent-visual-review.md',
     'independent-technical-review.md', 'contact_sheet.png'}
    | {view+'.png' for view in VIEWS}
    | {view+'_comparison.png' for view in VIEWS}
    | {mode+'_checks.json' for mode in MODES}))
CRITERIA = ('wing_primary', 'wing_layers', 'body_layers', 'tail_layers',
            'face_finish', 'symmetry', 'gesture_binding', 'function_preserved',
            'history_preserved')
NEW_SOURCES = (
    'design/wings_feathers.json',
    'scripts/blender/30_wings_feathers.py',
    'scripts/blender/legacy/30_wings_feathers.py',
    'scripts/blender/feathers_geometry.py',
    'scripts/blender/feathers_checks.py',
    'scripts/blender/feathers_evidence.py',
    'scripts/feathers_review.py',
    'scripts/feathers_contracts.py',
    'scripts/feathers_gate.py',
)
SOURCES = tuple(sorted(set(PREVIOUS_SOURCES).union(NEW_SOURCES)))
REFERENCE_NAMES = DELIVERY_INVENTORIES['face_v01']['reference_sha256']
REFERENCE_AUTHORITY = (
    {'file': '00_original_logo.png', 'rank': 1},
    {'file': '07_turnaround_technical.png', 'rank': 2},
    {'file': '08_parts_lookdev_technical.png', 'rank': 3},
)

# Filled from Git 966b7f0 blobs, with true SHA-256 OIDs for LFS files. Each
# currently materialized file was independently matched before recording it.
ADDED_PREDECESSOR_SHA256 = {'blender/scene/owli_review_fixes_v01.blend': '8685fc054428ec848f20a922c995487f9ac4a2797cbe3713eaeb5e364b02e8fb',
 'design/review_fixes.json': '59dc780738e4e0a26e3e430ecc4c14cf3eda36b6d29cf4689f7ccaecb9824c3a',
 'scripts/audit_review_fixes_history.py': 'd48b1bc3e15f208dffb3ca7b99167292af3154e987886c1bf782de6ce90cdcc2',
 'scripts/blender/review_fixes_checks.py': '8f1e0d3c8bc2f636b6999960e61cced361e1eb427bfee4d4a9b822f6a86e5de6',
 'scripts/blender/review_fixes_evidence.py': '4e8cd5a7e420303264041981297fc273303460127b23ec4d965baaa46f56c431',
 'scripts/blender/review_fixes_geometry.py': 'cb8f557dbbb7c825d11264fb59856e43d3c9f079e71d8d94156d5f83f4662c5d',
 'scripts/delivery_gates.py': '7c1473bd6a272a0f0451f859b74935235b3b247c721d5166b32046dff7251bcc',
 'scripts/delivery_shapes.py': '7e68b681b9b375fb09dcecf0efb5fbea49e4c52a5ee3b6d154ca031bc75e3eda',
 'scripts/evidence_contracts.py': '8155c2dc1ace94fa1e3dfdfa8afc1ec115708f2918f047da438a2f64ef9d1627',
 'scripts/history_gate.py': 'f5afb5a9f5dac6b64a556ddc02bf010dee45feb48ef9643d84cd28d8c2e5f32b',
 'scripts/review_fixes_contracts.py': '4db816a2136acf6f281beca2122ee94ce646fa32cfa086ad556255312bb58ddb',
 'scripts/review_fixes_gate.py': 'caf23e02d9966ddb00da92f5f631e07b3e080ca2790b8db89e7189d1a148ebef',
 'scripts/review_fixes_review.py': 'cf271609451f48d40d383734d4742b0e4752b76fd82c46695c21711382f544ef',
 'scripts/validate_project.py': '9a427188d6e806cd930a95dec7ddb2b7769d7696657dfbfc32a1dc33398b9a20',
 'validation/reviews/review_fixes_v01/.gitattributes': '969460aaa0c55ba72617714a75087807b6fc97800fdb333734867f526cb77824',
 'validation/reviews/review_fixes_v01/README.md': '0d5e22b508b545181b60241cc3d65667f21125dc98e357c8305aafdb0a3a0f1c',
 'validation/reviews/review_fixes_v01/VAL_3Q.png': 'aece67db89b615666fc56eb7ccce679ce0b799bb08275a550dc6dcf8a05e4a3f',
 'validation/reviews/review_fixes_v01/VAL_3Q_comparison.png': 'b21dcfa244783c4b5c72e85ba0cfa1989952830919fdc78937a95bba65900e21',
 'validation/reviews/review_fixes_v01/VAL_BACK.png': '0d53699a408a29f4370a205f7ae66339212530e7e3caea2d4228c1e47e913bfa',
 'validation/reviews/review_fixes_v01/VAL_BACK_comparison.png': '0a3580d3cfcee473716d138a3c5cc83ccf0878fea5983642f2079ef4e14faed2',
 'validation/reviews/review_fixes_v01/VAL_FRONT.png': 'aae72c5f212ba017c23d146dfcb1bf1035ec4aa9f79137c347a6f534d336ed38',
 'validation/reviews/review_fixes_v01/VAL_FRONT_comparison.png': '004508220c0bf16c0c74561e3a67231c1f90623db9d17372ca7e3d18a51e51ad',
 'validation/reviews/review_fixes_v01/VAL_LEFT.png': 'd7d6eaf0137155e84407382ed7b6d158ad93a4272d8586c9103420dc03bcaca0',
 'validation/reviews/review_fixes_v01/VAL_LEFT_comparison.png': '77143ef7814bbb5fb439690ff58f817afe6d764c3ed1be85e393df00c2e68779',
 'validation/reviews/review_fixes_v01/baseline_vs_corrected.png': '1a5771d631658d223650732968ac072ba4453956e561f3d8e3cc9a0c713d2a4d',
 'validation/reviews/review_fixes_v01/build.log': '382ea15f2f52e496680c334e7d248720f3a339d9ee529e100f783c923bb3b6c0',
 'validation/reviews/review_fixes_v01/build_checks.json': '4ab0413cdac39678cd81920eb7598fffb8c7a7fb3296bcf1bfb7a754894944ef',
 'validation/reviews/review_fixes_v01/check-compileall.log': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
 'validation/reviews/review_fixes_v01/check-doctor.log': 'ed7329977d8b398bb545a6be22d3e92fdc8af94bda8568165e1a423c05e51f7f',
 'validation/reviews/review_fixes_v01/check-smoke.log': 'e7d5886ae05243496c657839945fdb3d5f18cba355dc40fb975f590fa059e89a',
 'validation/reviews/review_fixes_v01/check-tests.log': '3c84a4b19a498753381dad663a8a5f5d83ca2f613e13305f0e4ea402f38f7238',
 'validation/reviews/review_fixes_v01/check-validate.log': '134e362fa4246889321d8c8f96f2fe6596562ae03b695b7d9839b0d6ef8155ae',
 'validation/reviews/review_fixes_v01/command-results.json': '25a636ac34240c992b81d33fffd66b2ab906202b1ce4d358430b3da0638f0ba8',
 'validation/reviews/review_fixes_v01/contact_sheet.png': '72030256a1762dcd185c33cf493f05ffbdd7a4997eaf7a71363a66d4e62de1c5',
 'validation/reviews/review_fixes_v01/evidence/baseline/VAL_3Q.png': '798923eb6cff7db4b8551e0e824cd3e021b7373e88729c2c5210ccf635f00042',
 'validation/reviews/review_fixes_v01/evidence/baseline/VAL_BACK.png': 'c4c9ad7103e343799c85c62cf8722714b8810994f60854e21e468270e1fe391e',
 'validation/reviews/review_fixes_v01/evidence/baseline/VAL_FRONT.png': '8ffa080e1f0f6762897fc012d29c21f6a65224afa50973bf105ae91cbf02d506',
 'validation/reviews/review_fixes_v01/evidence/baseline/VAL_LEFT.png': '95f918d5f16f00660426534c7b537b64c55227487c6f74121d01ae913b86c151',
 'validation/reviews/review_fixes_v01/evidence/beak_open/VAL_3Q.png': '45f6c87e20678d6d8879514036e271c32d4986c3868a21855575400bdfea8856',
 'validation/reviews/review_fixes_v01/evidence/beak_open/VAL_BACK.png': 'cd0621be11615625b60483dfb11850acee48d14748f05eeb15c9aef7ac732bfc',
 'validation/reviews/review_fixes_v01/evidence/beak_open/VAL_FRONT.png': '8aa87ce1c3ee609516d92dd2deb943abe56049442d66579550c29e08d2c78eca',
 'validation/reviews/review_fixes_v01/evidence/beak_open/VAL_LEFT.png': 'c421e5ff2018b30c95903d85c50fd8c1d8f7bf363405197bbefc17e00fdd186c',
 'validation/reviews/review_fixes_v01/evidence/blink/VAL_3Q.png': 'c9cb21029e547d3401ac9759369be2c2a6bf1d3fdd4a2884bea4a28f6fa4034f',
 'validation/reviews/review_fixes_v01/evidence/blink/VAL_BACK.png': '35f3a403018fd4926a8de18cbfc8d818bca9bd226c40425ef62226f0bb12a9c6',
 'validation/reviews/review_fixes_v01/evidence/blink/VAL_FRONT.png': '4f9f5afef3265d86a8af59811dd3f78b40ed6b9f56490f3d13d9d6cbb0d0a267',
 'validation/reviews/review_fixes_v01/evidence/blink/VAL_LEFT.png': 'dce9daeb5c95f6731d91a23d8e3410a6e917679252e913ca28941ea29f47d999',
 'validation/reviews/review_fixes_v01/evidence/live_neutral/VAL_3Q.png': '902d50a8c9f54f3557671b3bfd99139ce543cfe263d7069fd32e56edceca8c98',
 'validation/reviews/review_fixes_v01/evidence/live_neutral/VAL_BACK.png': 'b75841436e4c88385e12e91c39c1b4854f88b7b9fd51161531bbff6921dfe263',
 'validation/reviews/review_fixes_v01/evidence/live_neutral/VAL_FRONT.png': '2213c0d47b32cbcf2a45412a48309122d739330bcfa098768bda1de3fe2d72e0',
 'validation/reviews/review_fixes_v01/evidence/live_neutral/VAL_LEFT.png': '0a48c4300fe408c0d0a5bff329bea4361b962f1a58abe25f503352f3997dae2d',
 'validation/reviews/review_fixes_v01/evidence/neutral/VAL_3Q.png': 'c44135a3d4e1a7b2504a5d5bfc5e819b4505078b474f1223949d16c4cf31c358',
 'validation/reviews/review_fixes_v01/evidence/neutral/VAL_BACK.png': '056b06526698dc96ce32d33ef67f3631f9b177d916e58ed17daad1a5aec9ce2f',
 'validation/reviews/review_fixes_v01/evidence/neutral/VAL_FRONT.png': '64aa12e92dc4da7b22da3ceff44636f91fd21fadb07935bc53a56d8abae5d523',
 'validation/reviews/review_fixes_v01/evidence/neutral/VAL_LEFT.png': 'd07a57f99cda23794a207345526acba59d26f1e3c5fed3e1f6cbef490a6f1974',
 'validation/reviews/review_fixes_v01/evidence/reload_a/VAL_3Q.png': '3360ec2d607144af8a8caad0c67315a18ab965348ec09d366599714e4c9e8253',
 'validation/reviews/review_fixes_v01/evidence/reload_a/VAL_BACK.png': 'a56527e9f3682c93a3b4afe57ae7ff44f2cfaecc120253f575a81ae31a8f2e78',
 'validation/reviews/review_fixes_v01/evidence/reload_a/VAL_FRONT.png': 'ffb77246c9ad4e88f8dac9b1197f64db3f621bfdd41742683171a12dd70035c3',
 'validation/reviews/review_fixes_v01/evidence/reload_a/VAL_LEFT.png': '326d67d1c15e63857c814333273399ec43fad4548eebc33332c2289cc11283ef',
 'validation/reviews/review_fixes_v01/evidence/reload_b/VAL_3Q.png': 'aece67db89b615666fc56eb7ccce679ce0b799bb08275a550dc6dcf8a05e4a3f',
 'validation/reviews/review_fixes_v01/evidence/reload_b/VAL_BACK.png': '0d53699a408a29f4370a205f7ae66339212530e7e3caea2d4228c1e47e913bfa',
 'validation/reviews/review_fixes_v01/evidence/reload_b/VAL_FRONT.png': 'aae72c5f212ba017c23d146dfcb1bf1035ec4aa9f79137c347a6f534d336ed38',
 'validation/reviews/review_fixes_v01/evidence/reload_b/VAL_LEFT.png': 'd7d6eaf0137155e84407382ed7b6d158ad93a4272d8586c9103420dc03bcaca0',
 'validation/reviews/review_fixes_v01/foot_corners.json': '779d1fe35ab2e4291a0b50bba526319736231f5a4acf2170ec4e8715f6c7e97f',
 'validation/reviews/review_fixes_v01/foot_corners.log': 'bbe5b0b5215504376810bf05f123a46bb3db5149cb8832399e19579b968be3b8',
 'validation/reviews/review_fixes_v01/history-git-audit.json': '670cb5a2814382e5293962a99d8ff15560f2592fe8ffca56620fae32b8ecb1ac',
 'validation/reviews/review_fixes_v01/independent-gates-evidence.json': '1c7942c1b8606db3db1e43ef8a2052bd412dcea59782d0236e9603790772c7af',
 'validation/reviews/review_fixes_v01/independent-gates-review.md': 'ff7b25bf6ba2eb38bf40c482206cab7b71bb1b8eda0b4c51764ad43225308517',
 'validation/reviews/review_fixes_v01/independent-visual-review.md': '4cb38aa5562724ce5e85ac03179bdf5250ee67f5d5f4cc462b9c2a5a555a4288',
 'validation/reviews/review_fixes_v01/make_comparison.py': '74e2211a7a1f75a17da525f9895358cf12856c153d8c74d4fd9e1b8ff5844df9',
 'validation/reviews/review_fixes_v01/reload_a.log': '3bee97bad3ba3a091b64ea21084a92266b00bf108592191d71404f9f094fc319',
 'validation/reviews/review_fixes_v01/reload_a_checks.json': 'f80c6739182b95a9717e6459e2bc216e9fa5227a928cb71184b9b416aced837a',
 'validation/reviews/review_fixes_v01/reload_b.log': 'ca36a63b6b0b9a0b07dd955980328eec4e0d7b7d0f60bae2e14a2c8af852141c',
 'validation/reviews/review_fixes_v01/reload_b_checks.json': 'f80c6739182b95a9717e6459e2bc216e9fa5227a928cb71184b9b416aced837a',
 'validation/reviews/review_fixes_v01/report.md': '0f041022a547584bbb9377537cfc2b26709cbf8f429dd052f2d535ceb715d9d2',
 'validation/reviews/review_fixes_v01/review.json': 'cbe87f6c893a97b0c5577764cdfcdef83865043fd535a029fe897798676160ec',
 'validation/reviews/review_fixes_v01/saved_build.log': '1be448c9cae5de9b85c901807e2a2cfc1a691771a35c68e317a6c36402b32917',
 'validation/reviews/review_fixes_v01/saved_build_checks.json': 'f80c6739182b95a9717e6459e2bc216e9fa5227a928cb71184b9b416aced837a',
 'validation/reviews/review_fixes_v01/verification.json': '756a60970e6ed69e010c2389fe1a78aa63e572324a93d293d053b278f5fe586b'}
PROTECTED_SHA256 = dict(PREVIOUS_PROTECTED_SHA256, **ADDED_PREDECESSOR_SHA256)

ARCHIVED_STAGE_SHA256 = '603d304e7b5b2e24e1fd8903164f66f36cb4520b17065ea60a4dc536ad3a1d57'
