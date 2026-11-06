# Changelog

## [3.0.0](https://github.com/balloobbot/Home_Assistant_Integration/compare/3.2.0...3.0.0) (2026-11-06)


### ⚠ BREAKING CHANGES

* change domain to opendisplay
* **plot:** Lines now break at null/unavailable values by default. To restore previous behavior, set span_gaps: true per entity.
* existing camera entities automatically migrated to image entities

### Features

* accept a direct image URL in the upload_image service ([ef91895](https://github.com/balloobbot/Home_Assistant_Integration/commit/ef918955c89a4a7bc2d77e3ecfc70c301584e038))
* add a connectivity binary sensor ([a7635e7](https://github.com/balloobbot/Home_Assistant_Integration/commit/a7635e71f98d4ade62733da583b0c3cec57909f9))
* add a refine dithering option to image uploads ([3df2171](https://github.com/balloobbot/Home_Assistant_Integration/commit/3df21710dfd5374e22984a73fbf0b86b8704231b))
* add activate_led and activate_buzzer services ([c66b93d](https://github.com/balloobbot/Home_Assistant_Integration/commit/c66b93dae2add473a70a4850db8568343b91a888))
* Add AP model string instead of hardcoded "esp32" ([9d702b2](https://github.com/balloobbot/Home_Assistant_Integration/commit/9d702b2ecebc30b45102f589e735fd1157b3fc24))
* add configuration link for AP and OEPL BLE devices ([5a1e8a5](https://github.com/balloobbot/Home_Assistant_Integration/commit/5a1e8a5ace9737c91ff56d95b5f5280a306a44c2))
* add configuration link for ATC BLE tags ([4d85959](https://github.com/balloobbot/Home_Assistant_Integration/commit/4d859596ecb410909ce4acfffe0ca0383d365593))
* add drawcustom service using odl-renderer ([7f4226b](https://github.com/balloobbot/Home_Assistant_Integration/commit/7f4226ba6965ed4683b0196c4b69fb499a11884f))
* add experimental update entity to OEPL BLE devices ([cbcd2ae](https://github.com/balloobbot/Home_Assistant_Integration/commit/cbcd2ae2445f54338154ccc4fb40f608819e9b32))
* add firmware update entity ([c83721e](https://github.com/balloobbot/Home_Assistant_Integration/commit/c83721ebbc2f6ce9fc2977b8ce0169761fa50478))
* add image entity showing last rendered display content ([e1b5c9e](https://github.com/balloobbot/Home_Assistant_Integration/commit/e1b5c9ec097e025d8bb01af8e0e548d1205ec497))
* add native Bluetooth Low Energy (BLE) support for ATC BLE Tags ([24e31d9](https://github.com/balloobbot/Home_Assistant_Integration/commit/24e31d9b64b912367416e628a9b6f2df41eff377))
* add play_melody service for buzzer melodies ([79faf08](https://github.com/balloobbot/Home_Assistant_Integration/commit/79faf08633be8ce30261d3cb8128167385088cfa))
* add reachability reason to device-not-found errors ([e30e959](https://github.com/balloobbot/Home_Assistant_Integration/commit/e30e959f439d050aa28b187d1939593a4ced040f))
* add RSSI and last-seen sensors to all devices ([9001078](https://github.com/balloobbot/Home_Assistant_Integration/commit/9001078c3cf5bbd9e3dfd1bdcafb2bd49c413dba))
* Add Show timestamp switch to the AP device ([50583d8](https://github.com/balloobbot/Home_Assistant_Integration/commit/50583d8e6820597c34c4616c3fe209ebe74516ec))
* Add Show timestamp switch to the AP device ([54f66bf](https://github.com/balloobbot/Home_Assistant_Integration/commit/54f66bf236f16e6b4ccd6207109bf7be40f0de75))
* add tag alias text box ([bfef731](https://github.com/balloobbot/Home_Assistant_Integration/commit/bfef731c716073c7a834442ffda5508d54c6154a))
* add tag deep sleep button ([a8b9b61](https://github.com/balloobbot/Home_Assistant_Integration/commit/a8b9b61cdc015e3c41e4daf0b8ebe11a9cb7393e))
* add touch event entities for OpenDisplay touch controllers ([8f52faa](https://github.com/balloobbot/Home_Assistant_Integration/commit/8f52faa78a31095e7da81de57de03e444ec06418))
* add write_nfc action ([c6a1992](https://github.com/balloobbot/Home_Assistant_Integration/commit/c6a1992112c4835217f818a9f1e40b6935bb5cea))
* add write_nfc service metadata and translations ([f5fe60e](https://github.com/balloobbot/Home_Assistant_Integration/commit/f5fe60e8c5a7ab74edfbfa38c0e7bb383511f6ef))
* added support for labels in "Draw Custom Image" ([e64659b](https://github.com/balloobbot/Home_Assistant_Integration/commit/e64659bc2f127b8b72708f21f604790b1e6880b2))
* **arc:** add arc draw type ([ff15176](https://github.com/balloobbot/Home_Assistant_Integration/commit/ff15176c1a3428b4b5038bb480ae574716d84438))
* **binary_sensor:** add WiFi (LAN) status sensor with IP attribute ([96699da](https://github.com/balloobbot/Home_Assistant_Integration/commit/96699da1c95506ec4adc058baec433d12ef97260))
* **ble:** add direct write for OEPL_BLE ([584bd69](https://github.com/balloobbot/Home_Assistant_Integration/commit/584bd694dbf27f7741184daa2cc585c13390ecf0))
* **ble:** Add splash screen when adding BLE display to HA ([7758143](https://github.com/balloobbot/Home_Assistant_Integration/commit/77581438638090c9cc889492e161b25ed00198b0))
* **ble:** add temperature sensor to ble devices ([3e19f29](https://github.com/balloobbot/Home_Assistant_Integration/commit/3e19f2949a30f85ef27b7235207897239bb461aa))
* **BLE:** Added support for OEPL firmware ([da5c1b3](https://github.com/balloobbot/Home_Assistant_Integration/commit/da5c1b39d115969c242da94b3a08f9385ac4c2aa))
* **ble:** enhance BLE device handling with firmware and temperature updates ([de78f2b](https://github.com/balloobbot/Home_Assistant_Integration/commit/de78f2bf292492f89a93e09393a64ecda6b35ab4))
* **ble:** process-global per-MAC connection lock with contention WARNING ([58b75d4](https://github.com/balloobbot/Home_Assistant_Integration/commit/58b75d4fda82e27c0000b19a4524a6dfdf4f5e82))
* bound connect paths with deadlines and surface auth failures ([c5792ea](https://github.com/balloobbot/Home_Assistant_Integration/commit/c5792ea9b46bec9fac20bd8a22d87c9ddfa77ad3))
* bound connection lifetime with a wall-clock deadline; pin pipe-partial ([0f96fe5](https://github.com/balloobbot/Home_Assistant_Integration/commit/0f96fe5488f7ca92f591154d6d146eee92b0723e))
* bump py-opendisplay to 7.9.0 ([5bb2776](https://github.com/balloobbot/Home_Assistant_Integration/commit/5bb2776ee3339bf43b825063210bb16650dec6bb))
* **config-flow:** add DHCP discovery for AP devices ([c107abb](https://github.com/balloobbot/Home_Assistant_Integration/commit/c107abb6cfcd1988a22ea85ec806f15646db1deb))
* **debug_grid:** add debug grid draw type for layout visualization ([500f506](https://github.com/balloobbot/Home_Assistant_Integration/commit/500f5060fbb5e25cc6e23b745f0eb181ed2c4d45))
* defer BLE connect until discovery is confirmed ([43bc044](https://github.com/balloobbot/Home_Assistant_Integration/commit/43bc0447f80e4d15e614922e4fd989747eb2e41e))
* don't offer nRF firmware OTA install (proxy-unreliable) ([b633a71](https://github.com/balloobbot/Home_Assistant_Integration/commit/b633a711220d7b2e0e745bccb59333d64aa2f129))
* **drawcustom:** add font manager ([4817d7d](https://github.com/balloobbot/Home_Assistant_Integration/commit/4817d7d7b2138c31e3744a5f998751a17106037d))
* drop board revision from hardware version ([2fad89d](https://github.com/balloobbot/Home_Assistant_Integration/commit/2fad89dd80642566d485f78742bf6f8a89629669))
* expose dizzy dithering in the service selectors ([f64e7ea](https://github.com/balloobbot/Home_Assistant_Integration/commit/f64e7ea9111051503840f1a7cac4f4ea77d3f4f3))
* expose SHT40 ambient temperature and humidity ([4ed7be8](https://github.com/balloobbot/Home_Assistant_Integration/commit/4ed7be8c6ef537f8f3739dbcbd5e5a982252d345))
* expose sliding-window transfer options (blocks_per_ack, max_queue_size) ([db82e98](https://github.com/balloobbot/Home_Assistant_Integration/commit/db82e98c225bc19072b74ccbd39c85e3dcff7fe4))
* **Hub:** Add automatic removal of deleted tags ([c7c5aaf](https://github.com/balloobbot/Home_Assistant_Integration/commit/c7c5aaff083f9ba7399132611d8c90d853c01e26))
* **Hub:** Tags are now all discovered on setup instead of having to wait for a checkin once. ([2164662](https://github.com/balloobbot/Home_Assistant_Integration/commit/21646629d6e36bd8079fb58fa1f895f4b57360fd))
* **image_decompressor:** added working g5 implementation ([4898286](https://github.com/balloobbot/Home_Assistant_Integration/commit/48982860370d50e8fea300e3c33905282a18935b))
* **image:** add image entity to BLE tags for preview ([01d3a74](https://github.com/balloobbot/Home_Assistant_Integration/commit/01d3a74c5d67f6cf564881126ebcae4ff3c560e9)), closes [#308](https://github.com/balloobbot/Home_Assistant_Integration/issues/308)
* **imagegen:** Add resize method for downloaded image ([13cc8ad](https://github.com/balloobbot/Home_Assistant_Integration/commit/13cc8ad9df44acf73e18673d8abf52f9c0c8a591))
* **imagegen:** Add resize method for downloaded image ([6d139b9](https://github.com/balloobbot/Home_Assistant_Integration/commit/6d139b9a18cf27206784020489574f53b23c54b0))
* **imagegen:** Add warning on unsupported resize_method ([935a416](https://github.com/balloobbot/Home_Assistant_Integration/commit/935a4168794c7e11a3ffd44a68a62805bbf62f53))
* **imagegen:** support Home Assistant image/camera entities in dlimg type ([6c54f2c](https://github.com/balloobbot/Home_Assistant_Integration/commit/6c54f2c54fd67e2bbde8265d6c0535589e3d8096))
* implement BLE OTA firmware install (nRF + Silabs, proxy-safe) ([49c4408](https://github.com/balloobbot/Home_Assistant_Integration/commit/49c44082affc62ec38d9ae67eb9198b563e29032))
* **line:** add support for dashed lines with customizable dash and space lengths ([9143fc5](https://github.com/balloobbot/Home_Assistant_Integration/commit/9143fc5ac621697cc5c70e1601a5d24b6cab3222))
* make nRF firmware updates robust over a Bluetooth proxy ([1fc6e42](https://github.com/balloobbot/Home_Assistant_Integration/commit/1fc6e42d5c7308602f5e8e76a788c4d4671c052c))
* partial refresh support via py-opendisplay 7.11.1 ([350bf04](https://github.com/balloobbot/Home_Assistant_Integration/commit/350bf04bb5357240d59e03f75939fd50930e01c3))
* partial refresh support via py-opendisplay 7.11.1 ([c01e46e](https://github.com/balloobbot/Home_Assistant_Integration/commit/c01e46e9c487a0a0f27091aaa914c490e38fc751))
* phase 1 - sleep awareness, availability, setup-from-cache ([48e4d8b](https://github.com/balloobbot/Home_Assistant_Integration/commit/48e4d8b581382f988f79d17e9dc2f60d849f48e3))
* phase 2 - delivery manager and queued uploads ([3ff006b](https://github.com/balloobbot/Home_Assistant_Integration/commit/3ff006bb3a500d43f3c2acfde2f6d950cb6cb241))
* phase 3 - OTA gating and sleep diagnostics ([91daf42](https://github.com/balloobbot/Home_Assistant_Integration/commit/91daf421d292f208654c182cc9ade028004e816e))
* **plot:** add line_style parameter, which is closer to HAs rendering. ([57c0c80](https://github.com/balloobbot/Home_Assistant_Integration/commit/57c0c801aeacaa5a1694a2715f74d69a3cd0331a))
* **plot:** add span_gaps parameter to control line connections across null values ([42cc6a7](https://github.com/balloobbot/Home_Assistant_Integration/commit/42cc6a7c74a22f084c1dcc83eedfc89ac5e573c1)), closes [#148](https://github.com/balloobbot/Home_Assistant_Integration/issues/148)
* **polygon:** add polygon draw type ([9e9f689](https://github.com/balloobbot/Home_Assistant_Integration/commit/9e9f6899b38112e989fd1f0b7e2ec9506211dcad))
* probe before queue for image sends to probably-asleep devices ([aa108bc](https://github.com/balloobbot/Home_Assistant_Integration/commit/aa108bc7e6221da32f7bc4d58a40d5ac50edc6f9))
* probe before queue for sleeping devices ([4398e01](https://github.com/balloobbot/Home_Assistant_Integration/commit/4398e01fbf5e29349a2433ebb2f00e941e852e9a))
* **quality_scale:** add reconfigure flow for AP host updates ([fc36480](https://github.com/balloobbot/Home_Assistant_Integration/commit/fc36480eb638dd4ae3897fa8d33e56bd935b90b8))
* raise delivery deadline to 600s, fail loudly, cap retries at 5 ([655ac16](https://github.com/balloobbot/Home_Assistant_Integration/commit/655ac16cdfae007c86c3dbb8d57467a7228041d5))
* re-sync firmware/config when the device reboots ([2b785d7](https://github.com/balloobbot/Home_Assistant_Integration/commit/2b785d7a181bd73b228c72c59fafdd7cf8b2b54c))
* redesign activate_led service with 3 RGB color steps ([7bf7026](https://github.com/balloobbot/Home_Assistant_Integration/commit/7bf7026173f54558756812cf6ae2843592486fff))
* replace camera entities with image entities for tag content display ([5e76804](https://github.com/balloobbot/Home_Assistant_Integration/commit/5e768044f45e85d259adf68defa9861a56534039))
* replace custom integration with core opendisplay integration ([2ffb9ce](https://github.com/balloobbot/Home_Assistant_Integration/commit/2ffb9ce4c3cd2a80ddc6c5e26e211d64ad67463f))
* rewrite integration (3.0.0) ([6ddd641](https://github.com/balloobbot/Home_Assistant_Integration/commit/6ddd6410a323009f72bce7a41971195dc34ec244))
* **setup:** implement test-before-setup quality scale rule ([ab86276](https://github.com/balloobbot/Home_Assistant_Integration/commit/ab86276a2cd7143c5753e88ad925c47fb71df8c4))
* small performance improvement ([4d53a39](https://github.com/balloobbot/Home_Assistant_Integration/commit/4d53a39f3c1d6538ea90e5b904a0481e765f487d))
* support element rotation/mirror via odl-renderer 0.5.10 ([6aee85b](https://github.com/balloobbot/Home_Assistant_Integration/commit/6aee85bf1f8861888e28b3f39617893c07262818))
* **text:** add multiline support to parse_colors with proper anchor handling ([1be0e77](https://github.com/balloobbot/Home_Assistant_Integration/commit/1be0e77f49062248dc8bab090a0ccbd46c1cedf9))
* **translations:** add AI-generated translations for 8 languages ([bf2c689](https://github.com/balloobbot/Home_Assistant_Integration/commit/bf2c689d4609a6ba04da39fbe20f815355594c56))
* **translations:** add European Portuguese and document the workflow ([e4de62a](https://github.com/balloobbot/Home_Assistant_Integration/commit/e4de62a3efdf3ecb417a34b5ba7bd6238e45fdf3))
* **translations:** support any OpenAI-compatible provider ([eb940dd](https://github.com/balloobbot/Home_Assistant_Integration/commit/eb940dd2bafcfbe7ae869f6a5cd3192dec5d3d53))
* **ui:** improve dither selector with descriptive options ([dd71b02](https://github.com/balloobbot/Home_Assistant_Integration/commit/dd71b025c8d44538d80615b39bb8dc21cb79e535))
* **update:** optional GitHub token for firmware update checks ([2c13eb8](https://github.com/balloobbot/Home_Assistant_Integration/commit/2c13eb8c5fbf61322b9277ed74bc385c10452ef7))
* **upload:** add refresh_type parameter to support partial refresh ([a72c2bc](https://github.com/balloobbot/Home_Assistant_Integration/commit/a72c2bc56c78ee1bcfd1b3616dadf34b46d641b0))
* **upload:** add refresh_type parameter to support partial refresh ([864cc87](https://github.com/balloobbot/Home_Assistant_Integration/commit/864cc87f6510b52064d9d7a6a5148379307e1277))
* use per-device landing link for the Visit device button ([e0bc08f](https://github.com/balloobbot/Home_Assistant_Integration/commit/e0bc08f24f3beb5a0618a122d15921440d99450a))
* **wifi:** WiFi/LAN transport with mDNS discovery and BLE fallback ([6f98bec](https://github.com/balloobbot/Home_Assistant_Integration/commit/6f98becd6e5bce0b914bcb6c4d4f69a7fe33e1c8))
* wire up font_dirs in drawcustom, bump odl-renderer to 0.5.8 ([f103e04](https://github.com/balloobbot/Home_Assistant_Integration/commit/f103e04843a5020650303e1f9425483ff1f18c92))
* **workflow:** add GitHub Action to sync manifest version with release tag ([e83a70a](https://github.com/balloobbot/Home_Assistant_Integration/commit/e83a70a9b59f54e89f64dba0f9f0e0587e7bee83))
* **workflow:** add GitHub Action to sync manifest version with release tag ([6279043](https://github.com/balloobbot/Home_Assistant_Integration/commit/62790430d3be3a4bad23af3c839563ee62692d8a))


### Bug Fixes

* "TypeError: 'NoneType' object is not iterable" when providing no device_ids ([fa31b27](https://github.com/balloobbot/Home_Assistant_Integration/commit/fa31b279d6930ba05431233c6ca0caabec4143df))
* accept legacy drawcustom field values from pre-3.0 configs ([a30cd21](https://github.com/balloobbot/Home_Assistant_Integration/commit/a30cd212fced02c4b5983246c69218d091fb3db4))
* add bluetooth as a dependency in manifest.json ([6cc3fe5](https://github.com/balloobbot/Home_Assistant_Integration/commit/6cc3fe55ee3b03c5d1f7216c842783e0934bcc90))
* add touch event, drawcustom exception translations to en.json ([a02b4aa](https://github.com/balloobbot/Home_Assistant_Integration/commit/a02b4aa868380425c21a7e109bda6801c2837b5e))
* add version to manifest.json required for custom integrations ([e49f1c1](https://github.com/balloobbot/Home_Assistant_Integration/commit/e49f1c1aa03a55c91f7b861ae42ec3988521440f))
* attach the HACS zip from the release-please job ([bc1cf86](https://github.com/balloobbot/Home_Assistant_Integration/commit/bc1cf8694d52672ca28028d98cef660ad7e1c82c))
* **ble_atc:** fix garbled display on ATC BLE tags ([a46692e](https://github.com/balloobbot/Home_Assistant_Integration/commit/a46692e2530f8a0ff4605ad5150aebc11aeb2935))
* **ble_atc:** fix garbled display on ATC BLE tags ([a01e1a7](https://github.com/balloobbot/Home_Assistant_Integration/commit/a01e1a72381c23bc46be1d4fbffda8e1af15f9a4))
* **ble:** correct image dimensions for OEPL displays ([355c27b](https://github.com/balloobbot/Home_Assistant_Integration/commit/355c27b1c5d81034a2937c974d1be1956a039324))
* **ble:** update timestamp calculation and refactor ping_device function signature ([f51ccf7](https://github.com/balloobbot/Home_Assistant_Integration/commit/f51ccf79e69a6ed7a1bf6abe32d9eb18d6183b9d))
* bump py-opendisplay to 7.3.1 (90s uncompressed END ACK timeout) ([3b6f180](https://github.com/balloobbot/Home_Assistant_Integration/commit/3b6f180470c7c728e044fa00e6f22b472ec678b2))
* **ci:** correct include-v-in-tag to boolean value ([46be136](https://github.com/balloobbot/Home_Assistant_Integration/commit/46be13604b98ea873a421f3bd657df7a90c106a4))
* correct 6-color direct write mapping for spectra displays. ([4334081](https://github.com/balloobbot/Home_Assistant_Integration/commit/4334081702373711a64e790320963414968917aa)), closes [#309](https://github.com/balloobbot/Home_Assistant_Integration/issues/309)
* correct ap config updates and sleep window payload ([e7b6a16](https://github.com/balloobbot/Home_Assistant_Integration/commit/e7b6a16eba1dd2a29dcee13584b4aede86a5a653)), closes [#276](https://github.com/balloobbot/Home_Assistant_Integration/issues/276)
* correct dither selector option value types in services.yaml ([a334409](https://github.com/balloobbot/Home_Assistant_Integration/commit/a334409de1de6abd4e5bbe5f754fee81a1682c7f))
* correct drawcustom 90/270 rotation transposition ([27f9afa](https://github.com/balloobbot/Home_Assistant_Integration/commit/27f9afa32d0c90311c73cd2ffef56d68d63e1c96)), closes [#43](https://github.com/balloobbot/Home_Assistant_Integration/issues/43)
* correct except-tuple syntax for auth errors in config flow ([51f6fbd](https://github.com/balloobbot/Home_Assistant_Integration/commit/51f6fbd3f6e624944c7122071f8e29a2539b5c67))
* correctly label OEPL color schemes and model names. ([0860e02](https://github.com/balloobbot/Home_Assistant_Integration/commit/0860e022c444870a70801fc8eeb2a2bba4191e01))
* declare silabs-ble-ota explicitly in the manifest ([b27f123](https://github.com/balloobbot/Home_Assistant_Integration/commit/b27f123697a114e220f904df15e291ca609bfde9))
* **delivery:** report "auth" not a stale expiry when submitting while paused ([098704f](https://github.com/balloobbot/Home_Assistant_Integration/commit/098704f8842dc08c263f251c9bd575286a733669)), closes [#91](https://github.com/balloobbot/Home_Assistant_Integration/issues/91)
* **delivery:** stop the auth retry loop on a pending config resync ([3caca90](https://github.com/balloobbot/Home_Assistant_Integration/commit/3caca90461c8ddc9d2b9777accf2367750e54026)), closes [#91](https://github.com/balloobbot/Home_Assistant_Integration/issues/91)
* device name update from AP is reflected in HA ([a604afd](https://github.com/balloobbot/Home_Assistant_Integration/commit/a604afd172a74a3e254787c9861a90c8c0d2d95d))
* **drawcustom:** fix issue that causes HA to freeze when `tick_every` is 0 ([5e86176](https://github.com/balloobbot/Home_Assistant_Integration/commit/5e86176e9760a1e28dea2bebb6980bc6aeb00b22)), closes [#280](https://github.com/balloobbot/Home_Assistant_Integration/issues/280)
* **drawcustom:** ttl is now correctly converted to minutes ([e70703b](https://github.com/balloobbot/Home_Assistant_Integration/commit/e70703bb1ad5961119b3c8bbb523aedb5c26441d))
* **drawcustom:** typo fixed ([8d5f814](https://github.com/balloobbot/Home_Assistant_Integration/commit/8d5f8147acd08f6946340b86d77245d6aa4fcc98))
* entity-unavailable - mark entities unavailable when unreachable ([db92cd4](https://github.com/balloobbot/Home_Assistant_Integration/commit/db92cd4edd239f54c1432f1969ce312225a1b533))
* fetch camera and image sources from their still endpoint ([5589a94](https://github.com/balloobbot/Home_Assistant_Integration/commit/5589a940529ea17e71806bba4427745bb699129d))
* fix manifest for custom integration (documentation URL, issue_tracker, recorder dependency) ([5b9ffba](https://github.com/balloobbot/Home_Assistant_Integration/commit/5b9ffbabba43b1f320bf11c2bf6a1b048a749977))
* fix repo URL in update.py ([4ca46c5](https://github.com/balloobbot/Home_Assistant_Integration/commit/4ca46c523483f3fd21912e09aba77784e1d7b064))
* Fix tests and rename images ([#7](https://github.com/balloobbot/Home_Assistant_Integration/issues/7)) ([e2e64ee](https://github.com/balloobbot/Home_Assistant_Integration/commit/e2e64ee54603118ef901c7e0b32382389e026023))
* forward measured_palette to prepare_image in drawcustom/upload_image ([010174b](https://github.com/balloobbot/Home_Assistant_Integration/commit/010174b63c94276df8fdd58f132d31d530e1c4e4))
* **image:** fix rotation of preview image for ATC BLE tags ([ddba624](https://github.com/balloobbot/Home_Assistant_Integration/commit/ddba624b837880a39b26a3bf877bc8cdf2dbfbd3))
* include error details in upload failure message ([013cd03](https://github.com/balloobbot/Home_Assistant_Integration/commit/013cd03390d62ba89eaeedb484240c7a4af066fe))
* **init:** use async_add_executor_job for file operations ([cb3de17](https://github.com/balloobbot/Home_Assistant_Integration/commit/cb3de174bed299eb0088fe41188a1b781de0dd80))
* keep Home Assistant responsive while drawcustom renders ([f6941c9](https://github.com/balloobbot/Home_Assistant_Integration/commit/f6941c9b456a04cfd3608be367c1091f021847a6))
* loading tag types from GitHub, workflow for fallback_definitions ([#8](https://github.com/balloobbot/Home_Assistant_Integration/issues/8)) ([00a623c](https://github.com/balloobbot/Home_Assistant_Integration/commit/00a623cecd98d832dbb6dee81de358e1757f777c))
* make AP buttons use config entry IDs for unique IDs ([fe6f64c](https://github.com/balloobbot/Home_Assistant_Integration/commit/fe6f64cb9dc536fbc8d535c0f0af62b0f70fc5cc))
* mock serial and bluetooth modules in conftest.py for tests ([ce3c99b](https://github.com/balloobbot/Home_Assistant_Integration/commit/ce3c99b74dcd313586a305f9e1bf4122ad65eec4))
* **multiline:** parse percentage coordinates properly ([3a7ceb0](https://github.com/balloobbot/Home_Assistant_Integration/commit/3a7ceb0b7977fea64ffc808e1a27e901e860b47d))
* never set up the event platform for a base model ([4929c5c](https://github.com/balloobbot/Home_Assistant_Integration/commit/4929c5c4b8f4ea18b502a7a17a253540894b8235))
* **oepl_ble:** fix incorrectly displayed firmware for OEPL BLE devices ([5e421f8](https://github.com/balloobbot/Home_Assistant_Integration/commit/5e421f8f87c60f5db1a3c61620f10253b1ed0aee)), closes [#307](https://github.com/balloobbot/Home_Assistant_Integration/issues/307)
* Offload image prepare to executor, keep BLE transfer on the loop ([db96d11](https://github.com/balloobbot/Home_Assistant_Integration/commit/db96d11bb58afc1d2591dbbe5825d20cad4ae1dd))
* only offer devices that advertise as OpenDisplay ([02e5e79](https://github.com/balloobbot/Home_Assistant_Integration/commit/02e5e790053edf6a0077a0b87e62bfac591974a1))
* pass entity id to set led pattern and ignore missing led colors ([a55360c](https://github.com/balloobbot/Home_Assistant_Integration/commit/a55360c2d00d9fc33721364cd1174de49fa1b06c))
* **plot:** update time retrieval to use local time instead of UTC ([a2d0045](https://github.com/balloobbot/Home_Assistant_Integration/commit/a2d00455704fc25a21d08682462319089cd95fbc))
* **plot:** update time retrieval to use local time instead of UTC ([03eb743](https://github.com/balloobbot/Home_Assistant_Integration/commit/03eb74393a17452df0d79b8d6e69cd435e908d5e))
* poll latest firmware version on load and override should_poll ([388dc72](https://github.com/balloobbot/Home_Assistant_Integration/commit/388dc721c40a96cbf8c6335973f2f86b4d856cf7))
* properly set name on discovery of BLE devices ([b2148fb](https://github.com/balloobbot/Home_Assistant_Integration/commit/b2148fb04e91bcab46885fd0e902ed65c7d21b5d))
* **quality_scale:** allow removing stale BLE devices via device registry to comply with the stale-devices rule ([cea60e8](https://github.com/balloobbot/Home_Assistant_Integration/commit/cea60e8937863b44dad9b85a534703dfa61c9729))
* **quality_scale:** surface camera migration via repairs (repair-issues rule) ([dd0bf28](https://github.com/balloobbot/Home_Assistant_Integration/commit/dd0bf282135ce54974f00df06d37571c0a2d6eba))
* redact the AES key and device identity from diagnostics ([e831ba7](https://github.com/balloobbot/Home_Assistant_Integration/commit/e831ba7a12a50a533d87c5b2be80b4b8c3e02fbb))
* reduce BLE concurrent uploads and improve protocol reliability ([a190a17](https://github.com/balloobbot/Home_Assistant_Integration/commit/a190a1733dd848e7ea257a1102836c0fbca89fc7))
* register the mDNS service type in the manifest ([8096fc4](https://github.com/balloobbot/Home_Assistant_Integration/commit/8096fc4b83252388f1296c9d4fa1ed8a22509053))
* remove examples from setled service ([d18606b](https://github.com/balloobbot/Home_Assistant_Integration/commit/d18606bf2ab96ef18b3965b46d403b3665945244))
* remove space from py-opendisplay requirement for hassfest ([ebfc791](https://github.com/balloobbot/Home_Assistant_Integration/commit/ebfc7918fb0dc94be0b2d903ab2c09058668d396))
* reorder bluetooth entry in manifest.json ([1f9c6bc](https://github.com/balloobbot/Home_Assistant_Integration/commit/1f9c6bc88f33b10189d4f8c91674829a6d5ad779))
* report the firmware patch version everywhere HA shows it ([0551502](https://github.com/balloobbot/Home_Assistant_Integration/commit/05515022ad7a3cb4a08ae09d3ee0887bc6353c77)), closes [#62](https://github.com/balloobbot/Home_Assistant_Integration/issues/62)
* require py-opendisplay&gt;=7.18.1 instead of an exact pin ([735ceb8](https://github.com/balloobbot/Home_Assistant_Integration/commit/735ceb8d201715997657dbb04476c8d347b8f3ee))
* **sensor:** source last_seen from the bluetooth stack, not the gated callback ([f440050](https://github.com/balloobbot/Home_Assistant_Integration/commit/f440050b0612e559bf3d0ff19f67002f3f1d7af4))
* **sensor:** source last_seen from the bluetooth stack, not the gated callback ([8dd7b85](https://github.com/balloobbot/Home_Assistant_Integration/commit/8dd7b85eaae422b5addd8aed075d0b23b97b272d))
* Serialize BLE access per tag with a per-MAC lock ([ec26a97](https://github.com/balloobbot/Home_Assistant_Integration/commit/ec26a97217c9ab723511dae30b5acd69440cbbe3))
* **services:** accept device_id as string or list ([b503563](https://github.com/balloobbot/Home_Assistant_Integration/commit/b5035631d797db2a381b6f5a38ac08f17b3ef9f7)), closes [#314](https://github.com/balloobbot/Home_Assistant_Integration/issues/314)
* **services:** remove deprecated device filters from target selectors ([6d8dbbb](https://github.com/balloobbot/Home_Assistant_Integration/commit/6d8dbbb0ffcecafde72e85eceb9402596409133c))
* **services:** remove target device selector from drawcustom ([9f4b662](https://github.com/balloobbot/Home_Assistant_Integration/commit/9f4b662dd797d62a4e0ceeb7fec15688c311fb2a))
* set has_entity_name on image entities and import helper ([f4c5c6b](https://github.com/balloobbot/Home_Assistant_Integration/commit/f4c5c6bddde5feab1e54185a74623d84a2e57f53))
* show the firmware patch version when py-opendisplay provides it ([c5c929d](https://github.com/balloobbot/Home_Assistant_Integration/commit/c5c929da4baf18c8b36b2376db341604f2a6e3a6))
* skip battery entities for externally powered devices ([c8ecc3b](https://github.com/balloobbot/Home_Assistant_Integration/commit/c8ecc3b8f9219cf8f8dc85347acf0845ea700d8a))
* stop scaling firmware minor version by 10 ([d00715f](https://github.com/balloobbot/Home_Assistant_Integration/commit/d00715f99d9ce91866196d6a4718a79ee82cba70))
* take camera and image snapshots from the entity directly ([9dd46e4](https://github.com/balloobbot/Home_Assistant_Integration/commit/9dd46e498746e93f5914111f1b29330757b8c15f))
* **tests:** Fix missing new parameters of drawcustom ([983ef6d](https://github.com/balloobbot/Home_Assistant_Integration/commit/983ef6d691cebd6edfbf4132c58a563398a4340f))
* **text:** allow color tags to span multiple lines in text elements ([c894eb0](https://github.com/balloobbot/Home_Assistant_Integration/commit/c894eb0d387462a98c74664fb4bf946c8e3f5b25))
* **text:** correct anchor alignment when using parse_colors ([36a346d](https://github.com/balloobbot/Home_Assistant_Integration/commit/36a346d52756ec1947191f36b940258ab5aea612)), closes [#242](https://github.com/balloobbot/Home_Assistant_Integration/issues/242)
* translate the setup errors ([9124594](https://github.com/balloobbot/Home_Assistant_Integration/commit/9124594124b071b86fa5168988e27586a6b9e54b))
* **translations:** more natural German terminology ([#104](https://github.com/balloobbot/Home_Assistant_Integration/issues/104)) ([4198741](https://github.com/balloobbot/Home_Assistant_Integration/commit/41987414a7072e86b4f3117ef6f3db5a968249e0))
* **translations:** report API failures with the cause and a next step ([9ae4a4d](https://github.com/balloobbot/Home_Assistant_Integration/commit/9ae4a4d8f5e9c266052e45cabf140f76826a10db))
* **translations:** use a NUL path separator instead of a dot ([d955ad1](https://github.com/balloobbot/Home_Assistant_Integration/commit/d955ad1fcc47314defd2b9ec14bdb1fd47d41b9f))
* typos ([ab1ffab](https://github.com/balloobbot/Home_Assistant_Integration/commit/ab1ffabace6a05ad40bf7ac74cdc441933ea22f6))
* update dry-run description for clarity ([5f998d0](https://github.com/balloobbot/Home_Assistant_Integration/commit/5f998d0db11bdbff83f0348426693e81da735bc0)), closes [#309](https://github.com/balloobbot/Home_Assistant_Integration/issues/309)
* update py-opendisplay to 7.16.0 ([516ff5c](https://github.com/balloobbot/Home_Assistant_Integration/commit/516ff5c95f0d79c029b925b0f595e48158717c3e))
* update py-opendisplay to 7.18.1 ([1ad2af9](https://github.com/balloobbot/Home_Assistant_Integration/commit/1ad2af9f2c42273cbf27b06acf1dfb9db1146471))
* **upload:** recreate MultipartEncoder for each retry attempt ([08adbf7](https://github.com/balloobbot/Home_Assistant_Integration/commit/08adbf70aec6d31c32dacaccea3b504c8d9bfdd8))
* use UpdateEntityDescription to avoid display_precision AttributeError ([2bed475](https://github.com/balloobbot/Home_Assistant_Integration/commit/2bed475a97344eec42fc87a1380eded8b2a65062))
* validate canvas dimensions to prevent PIL errors ([91e2b80](https://github.com/balloobbot/Home_Assistant_Integration/commit/91e2b8057a48467da34ef909ee7374ebd8f31373))
* **welcome_image:** fix missing colors ([0f480c1](https://github.com/balloobbot/Home_Assistant_Integration/commit/0f480c14ea721d52044843cb88a7b88c4d8bd297))
* wrong type hint in get_device_ids_from_label_id ([6c4c671](https://github.com/balloobbot/Home_Assistant_Integration/commit/6c4c671bba751a5a3539e2c03df01e25d3419bde))


### Performance Improvements

* keep drawcustom images as PIL until upload ([e72b609](https://github.com/balloobbot/Home_Assistant_Integration/commit/e72b609c2d0ffbe925033db5aeaf67863ce3608c))
* log drawcustom upload timings ([fc034d4](https://github.com/balloobbot/Home_Assistant_Integration/commit/fc034d4083513fe7e1c5ff83b49f2902632ba5f1))
* optimize BLE image preparation ([c6fabd1](https://github.com/balloobbot/Home_Assistant_Integration/commit/c6fabd1f619de2fcf0914eec33a87470ed1fb98b))
* select direct write compression by payload size ([1233130](https://github.com/balloobbot/Home_Assistant_Integration/commit/1233130780da1c6439c98a6273b7155709814c1d))


### Code Refactoring

* change domain to opendisplay ([74128a8](https://github.com/balloobbot/Home_Assistant_Integration/commit/74128a80812c9170bf9fbff30007b9faa9322b48))


### Miscellaneous Chores

* prepare 3.0.0 stable release ([882df96](https://github.com/balloobbot/Home_Assistant_Integration/commit/882df961b82c841ea4732ee9012bc4309afe887a))

## [3.2.0](https://github.com/OpenDisplay/Home_Assistant_Integration/compare/3.1.0...3.2.0) (2026-10-28)


### Features

* **update:** optional GitHub token for firmware update checks ([2c13eb8](https://github.com/OpenDisplay/Home_Assistant_Integration/commit/2c13eb8c5fbf61322b9277ed74bc385c10452ef7))


### Bug Fixes

* keep Home Assistant responsive while drawcustom renders ([f6941c9](https://github.com/OpenDisplay/Home_Assistant_Integration/commit/f6941c9b456a04cfd3608be367c1091f021847a6))

## [3.1.0](https://github.com/OpenDisplay/Home_Assistant_Integration/compare/3.0.2...3.1.0) (2026-10-12)


### Features

* add a connectivity binary sensor ([a7635e7](https://github.com/OpenDisplay/Home_Assistant_Integration/commit/a7635e71f98d4ade62733da583b0c3cec57909f9))
* add a refine dithering option to image uploads ([3df2171](https://github.com/OpenDisplay/Home_Assistant_Integration/commit/3df21710dfd5374e22984a73fbf0b86b8704231b))


### Bug Fixes

* only offer devices that advertise as OpenDisplay ([02e5e79](https://github.com/OpenDisplay/Home_Assistant_Integration/commit/02e5e790053edf6a0077a0b87e62bfac591974a1))
* require py-opendisplay&gt;=7.18.1 instead of an exact pin ([735ceb8](https://github.com/OpenDisplay/Home_Assistant_Integration/commit/735ceb8d201715997657dbb04476c8d347b8f3ee))
* take camera and image snapshots from the entity directly ([9dd46e4](https://github.com/OpenDisplay/Home_Assistant_Integration/commit/9dd46e498746e93f5914111f1b29330757b8c15f))
* translate the setup errors ([9124594](https://github.com/OpenDisplay/Home_Assistant_Integration/commit/9124594124b071b86fa5168988e27586a6b9e54b))
* update py-opendisplay to 7.18.1 ([1ad2af9](https://github.com/OpenDisplay/Home_Assistant_Integration/commit/1ad2af9f2c42273cbf27b06acf1dfb9db1146471))

## [3.0.2](https://github.com/OpenDisplay/Home_Assistant_Integration/compare/3.0.1...3.0.2) (2026-08-26)


### Bug Fixes

* declare silabs-ble-ota explicitly in the manifest ([b27f123](https://github.com/OpenDisplay/Home_Assistant_Integration/commit/b27f123697a114e220f904df15e291ca609bfde9))
* fetch camera and image sources from their still endpoint ([5589a94](https://github.com/OpenDisplay/Home_Assistant_Integration/commit/5589a940529ea17e71806bba4427745bb699129d))
* register the mDNS service type in the manifest ([8096fc4](https://github.com/OpenDisplay/Home_Assistant_Integration/commit/8096fc4b83252388f1296c9d4fa1ed8a22509053))
* update py-opendisplay to 7.16.0 ([516ff5c](https://github.com/OpenDisplay/Home_Assistant_Integration/commit/516ff5c95f0d79c029b925b0f595e48158717c3e))

## [3.0.1](https://github.com/OpenDisplay/Home_Assistant_Integration/compare/3.0.0...3.0.1) (2026-08-22)


### Bug Fixes

* attach the HACS zip from the release-please job ([bc1cf86](https://github.com/OpenDisplay/Home_Assistant_Integration/commit/bc1cf8694d52672ca28028d98cef660ad7e1c82c))
* **delivery:** report "auth" not a stale expiry when submitting while paused ([098704f](https://github.com/OpenDisplay/Home_Assistant_Integration/commit/098704f8842dc08c263f251c9bd575286a733669)), closes [#91](https://github.com/OpenDisplay/Home_Assistant_Integration/issues/91)
* **delivery:** stop the auth retry loop on a pending config resync ([3caca90](https://github.com/OpenDisplay/Home_Assistant_Integration/commit/3caca90461c8ddc9d2b9777accf2367750e54026)), closes [#91](https://github.com/OpenDisplay/Home_Assistant_Integration/issues/91)
* never set up the event platform for a base model ([4929c5c](https://github.com/OpenDisplay/Home_Assistant_Integration/commit/4929c5c4b8f4ea18b502a7a17a253540894b8235))
* redact the AES key and device identity from diagnostics ([e831ba7](https://github.com/OpenDisplay/Home_Assistant_Integration/commit/e831ba7a12a50a533d87c5b2be80b4b8c3e02fbb))
* **translations:** more natural German terminology ([#104](https://github.com/OpenDisplay/Home_Assistant_Integration/issues/104)) ([4198741](https://github.com/OpenDisplay/Home_Assistant_Integration/commit/41987414a7072e86b4f3117ef6f3db5a968249e0))

## [3.0.0](https://github.com/OpenDisplay/Home_Assistant_Integration/compare/v3.0.0-beta.10...3.0.0) (2026-08-21)


### Features

* rewrite integration (3.0.0) ([6ddd641](https://github.com/OpenDisplay/Home_Assistant_Integration/commit/6ddd6410a323009f72bce7a41971195dc34ec244))


### Miscellaneous Chores

* prepare 3.0.0 stable release ([882df96](https://github.com/OpenDisplay/Home_Assistant_Integration/commit/882df961b82c841ea4732ee9012bc4309afe887a))

## [2.0.2](https://github.com/OpenDisplay/Home_Assistant_Integration/compare/2.0.1...2.0.2) (2026-05-12)


### Performance Improvements

* keep drawcustom images as PIL until upload ([e72b609](https://github.com/OpenDisplay/Home_Assistant_Integration/commit/e72b609c2d0ffbe925033db5aeaf67863ce3608c))
* log drawcustom upload timings ([fc034d4](https://github.com/OpenDisplay/Home_Assistant_Integration/commit/fc034d4083513fe7e1c5ff83b49f2902632ba5f1))
* optimize BLE image preparation ([c6fabd1](https://github.com/OpenDisplay/Home_Assistant_Integration/commit/c6fabd1f619de2fcf0914eec33a87470ed1fb98b))
* select direct write compression by payload size ([1233130](https://github.com/OpenDisplay/Home_Assistant_Integration/commit/1233130780da1c6439c98a6273b7155709814c1d))

## [2.0.1](https://github.com/OpenDisplay/Home_Assistant_Integration/compare/2.0.0...2.0.1) (2026-02-25)


### Bug Fixes

* fix repo URL in update.py ([4ca46c5](https://github.com/OpenDisplay/Home_Assistant_Integration/commit/4ca46c523483f3fd21912e09aba77784e1d7b064))
* Fix tests and rename images ([#7](https://github.com/OpenDisplay/Home_Assistant_Integration/issues/7)) ([e2e64ee](https://github.com/OpenDisplay/Home_Assistant_Integration/commit/e2e64ee54603118ef901c7e0b32382389e026023))
* loading tag types from GitHub, workflow for fallback_definitions ([#8](https://github.com/OpenDisplay/Home_Assistant_Integration/issues/8)) ([00a623c](https://github.com/OpenDisplay/Home_Assistant_Integration/commit/00a623cecd98d832dbb6dee81de358e1757f777c))

## [2.0.0](https://github.com/OpenDisplay-org/Home_Assistant_Integration/compare/1.0.0...2.0.0) (2026-01-12)


### ⚠ BREAKING CHANGES

* change domain to opendisplay

### Code Refactoring

* change domain to opendisplay ([74128a8](https://github.com/OpenDisplay-org/Home_Assistant_Integration/commit/74128a80812c9170bf9fbff30007b9faa9322b48))

## Changelog
